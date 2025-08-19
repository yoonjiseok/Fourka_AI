"""
ML 가중치 Decay DAG
==================

목적: 사용자 피드백 기반 청크 가중치를 주기적으로 감소시켜 최신성 보장
스케줄: 매주 일요일 새벽 2시
작성자: 데이터팀
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
#from airflow.operators.email import EmailOperator
#from airflow.kubernetes.secret import Secret
#from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

# DAG 기본 설정
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email': ['data-team@company.com']  # 실제 환경에서는 팀 이메일
}

# DAG 정의
dag = DAG(
    'chunk_weight_decay',
    default_args=default_args,
    description='주간 Chunk 가중치 Decay 작업',
    schedule_interval='0 17 * * 6',  # 매주 일요일 2AM (cron 표현식) (KST 02:00 == UTC 토 17:00)
    catchup=False,  # 과거 실행 건너뛰기
    max_active_runs=1,  # 동시 실행 방지
    tags=['chunk', 'data-pipeline', 'weekly']
)

def create_decay_logs_table():
    """로그 테이블이 없으면 생성"""
    # 쿠버네티스에서는 Connection이 환경변수로 자동 설정됨
    hook = PostgresHook(postgres_conn_id='fourka_db')
    hook.run("""
        CREATE TABLE IF NOT EXISTS decay_logs (
            id SERIAL PRIMARY KEY,
            execution_date TIMESTAMP,
            chunks_before_decay INTEGER,
            chunks_after_decay INTEGER,
            affected_chunks INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

def send_decay_summary(**context):
    """Decay 실행 결과 요약 (Slack/이메일로 전송 가능)"""
    hook = PostgresHook(postgres_conn_id='fourka_db')
    
    # 최근 실행 결과 조회
    result = hook.get_first("""
        SELECT 
            chunks_before_decay,
            chunks_after_decay,
            affected_chunks
        FROM decay_logs 
        WHERE execution_date >= NOW() - INTERVAL '1 hour'
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    if result:
        before, after, affected = result
        summary = f"""
        📊 주간 가중치 Decay 완료
        
        ▫️ Decay 전 가중치 청크: {before}개
        ▫️ Decay 후 가중치 청크: {after}개  
        ▫️ 영향받은 청크: {affected}개
        ▫️ 실행 시간: {context['ds']}
        
        ✅ 정상 완료
        """
        print(summary)
        # 실제 환경에서는 Slack API 또는 이메일로 전송
        return summary
    else:
        raise ValueError("Decay 로그를 찾을 수 없습니다.")

# Task 1: 로그 테이블 생성
create_logs_table = PythonOperator(
    task_id='create_decay_logs_table',
    python_callable=create_decay_logs_table,
    dag=dag
)

# Task 2: 가중치 Decay 실행 (메인 작업)
decay_weights = PostgresOperator(
    task_id='decay_chunk_weights',
    postgres_conn_id='fourka_db',  # Airflow Connection ID
    sql='sql/decay_chunk_weights.sql',  # SQL 파일 경로
    autocommit=True,
    dag=dag
)

# Task 3: 실행 결과 요약 생성
generate_summary = PythonOperator(
    task_id='generate_decay_summary',
    python_callable=send_decay_summary,
    dag=dag
)

# Task 4: 이상 상황 시 알림 (선택적)
alert_on_anomaly = PostgresOperator(
    task_id='check_decay_anomalies',
    postgres_conn_id='fourka_db',
    sql="""
        -- 이상 상황 체크 (예: 너무 많은 청크가 decay된 경우)
        SELECT 
            CASE 
                WHEN affected_chunks > (chunks_before_decay * 0.5) 
                THEN 'ALERT: 50% 이상의 청크가 decay됨'
                ELSE 'OK'
            END as status
        FROM decay_logs 
        WHERE execution_date >= NOW() - INTERVAL '1 hour'
        ORDER BY created_at DESC 
        LIMIT 1;
    """,
    dag=dag
)

# Task 의존성 설정 (실제 데이터 파이프라인 패턴)
create_logs_table >> decay_weights >> [generate_summary, alert_on_anomaly]

# DAG 문서화 (Airflow UI에서 표시)
dag.doc_md = """
## ML 가중치 Decay 파이프라인

### 비즈니스 목적
- 사용자 피드백 기반 개인화 시스템의 최신성 유지
- 오래된 학습 데이터의 영향력 점진적 감소
- 시스템 성능 최적화

### 실행 주기
- 매주 일요일 새벽 2시 (서비스 사용량 최소 시간대)

### 모니터링
- 실행 결과는 decay_logs 테이블에 저장
- 이상 상황 시 데이터팀에 알림 발송
- Airflow UI에서 실시간 모니터링 가능

### 담당자
- 데이터팀 (data-team@company.com)
""" 