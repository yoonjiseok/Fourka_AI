# ✈️ FourKa AI - Apache Airflow 실행 가이드

## 📋 개요
**주간 Chunk 가중치 Decay 시스템**을 Apache Airflow로 구현한 데이터 파이프라인입니다.

### 🎯 주요 기능
- **주간 스케줄**: 매주 일요일 새벽 2시 자동 실행
- **가중치 Decay**: 7일 이상된 chunk 가중치를 5% 감소
- **로깅 시스템**: 실행 전후 상태 기록
- **이상 탐지**: 비정상적인 decay 패턴 감지

---

## 📋 사전 요구사항

### 필수 소프트웨어
```bash
# Docker 설치 확인
docker --version        # Docker version 20.0+
docker-compose --version # docker-compose version 1.28+
```

### 포트 확인
- **8080**: Airflow UI
- **5433**: Airflow 내부 PostgreSQL (충돌 방지)

---

## 🚀 빠른 시작

### 1. 환경설정

**✅ 현재 환경변수 방식으로 DB 연동이 자동 설정됩니다!**

기존 FastAPI 프로젝트의 `.env` 파일에 다음 환경변수가 있는지 확인:
```env
# 기존 FastAPI DB 연결 (이미 설정됨)
DB_URL=postgresql+asyncpg://user:password@host:port/database

# Airflow에서 자동으로 DB_URL을 파싱하여 연결 생성됩니다
# 별도 설정 불필요! 🎉
```

> **💡 참고**: `docker-compose.airflow.yml`에서 환경변수를 자동으로 파싱하여  
> `fourka_db` Connection을 생성합니다. 별도 설정이 불필요합니다!

### 2. Airflow 시작
```bash
# 실행 권한 부여
chmod +x airflow/start_airflow.sh

# Airflow 시작
./airflow/start_airflow.sh
```

> **💡 참고**: `requirements.txt` 파일은 참고용입니다. 
> 대부분의 패키지가 기본 이미지에 포함되어 있어 별도 설치가 불필요합니다.

### 3. 웹 UI 접속
- **URL**: http://localhost:8080
- **로그인**: admin / admin

### 4. DAG 활성화
1. DAG 목록에서 `chunk_weight_decay` 찾기
2. 왼쪽 토글 스위치 **ON**
3. DAG 이름 클릭 → Graph 탭에서 구조 확인

---

## 🧪 테스트 실행

### 수동 DAG 트리거
```bash
# 즉시 실행
docker exec airflow_webserver airflow dags trigger chunk_weight_decay
```

### 실행 상태 확인
```bash
# 웹 UI에서 확인하거나 CLI로 확인
docker exec airflow_webserver python -c "
from airflow.models import DagRun
from airflow.utils.session import provide_session

@provide_session
def check_runs(session=None):
    runs = session.query(DagRun).filter(DagRun.dag_id == 'chunk_weight_decay').order_by(DagRun.execution_date.desc()).limit(3).all()
    for run in runs:
        print(f'🔄 {run.run_id[-10:]}: {run.state}')

check_runs()
"
```

---

## 📊 시스템 모니터링

### 로그 확인
```bash
# Scheduler 로그
docker logs airflow_scheduler -f

# Webserver 로그  
docker logs airflow_webserver -f

# 전체 서비스 상태
docker-compose -f docker-compose.airflow.yml ps
```

### FourKa DB 연결 테스트
```bash
# 연결 테스트
docker exec airflow_webserver python -c "
from airflow.providers.postgres.hooks.postgres import PostgresHook
hook = PostgresHook(postgres_conn_id='fourka_db')
conn = hook.get_conn()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM chunk WHERE weight > 1.0')
print(f'✅ 연결 성공! 가중치 청크: {cursor.fetchone()[0]}개')
cursor.close()
conn.close()
"
```

### Decay 결과 확인
```bash
# decay_logs 테이블 확인
docker exec airflow_webserver python -c "
from airflow.providers.postgres.hooks.postgres import PostgresHook
hook = PostgresHook(postgres_conn_id='fourka_db')
conn = hook.get_conn()
cursor = conn.cursor()
cursor.execute('SELECT execution_date, chunks_before_decay, chunks_after_decay FROM decay_logs ORDER BY execution_date DESC LIMIT 5')
logs = cursor.fetchall()
print('📋 최근 Decay 실행 기록:')
for log in logs:
    print(f'  {log[0]}: {log[1]} → {log[2]} 개')
cursor.close()
conn.close()
"
```

---

## 🔧 설정 커스터마이징

### 스케줄 변경
**파일**: `airflow/dags/ml_weight_decay_dag.py` (34번째 줄)

```python
# 현재: 매주 일요일 2AM
schedule_interval='0 2 * * 0'

# 변경 예시:
schedule_interval='0 0 * * *'    # 매일 자정
schedule_interval='0 */6 * * *'  # 6시간마다
schedule_interval=None           # 수동 실행만
```

### Decay 조건 수정
**파일**: `airflow/dags/sql/decay_chunk_weights.sql` (23번째 줄)

```sql
-- 현재: 7일 이상
AND updated_at < NOW() - INTERVAL '7 days'

-- 변경 예시:
AND updated_at < NOW() - INTERVAL '3 days'   -- 3일로 단축
AND updated_at < NOW() - INTERVAL '14 days'  -- 2주로 연장
```

### Decay 비율 조정
**파일**: `airflow/dags/sql/decay_chunk_weights.sql` (17번째 줄)

```sql
-- 현재: 5% 감소 (×0.95)
weight = GREATEST(weight * 0.95, 1.0)

-- 변경 예시:
weight = GREATEST(weight * 0.90, 1.0)  -- 10% 감소
weight = GREATEST(weight * 0.98, 1.0)  -- 2% 감소
```

---

## 🔧 트러블슈팅

### 자주 발생하는 문제

#### 1. 포트 8080 충돌
```bash
# 포트 사용 확인
lsof -i :8080

# 다른 포트로 변경 (docker-compose.airflow.yml)
ports:
  - "8081:8080"  # 8081로 변경
```

#### 2. FourKa DB 연결 실패
```bash
# 환경변수 확인
docker exec airflow_webserver env | grep -E "(DB_URL|FOURKA)"

# 재시작
docker-compose -f docker-compose.airflow.yml restart
```

#### 3. DAG가 보이지 않음
```bash
# DAG 파일 확인
ls -la airflow/dags/

# Airflow 로그 확인
docker logs airflow_scheduler | grep -i error
```

#### 4. SQL 실행 오류
```bash
# SQL 문법 테스트
docker exec airflow_webserver python -c "
from airflow.providers.postgres.hooks.postgres import PostgresHook
hook = PostgresHook(postgres_conn_id='fourka_db')
# SQL 테스트 코드...
"
```

---

## 🛑 시스템 종료

### 안전한 종료
```bash
# Airflow 중지
docker-compose -f docker-compose.airflow.yml down

# 완전 정리 (데이터 포함)
docker-compose -f docker-compose.airflow.yml down -v
```

---

## 📚 DAG 구조 이해

```
chunk_weight_decay (매주 일요일 2AM)
├── create_decay_logs_table    # 로그 테이블 생성
├── decay_chunk_weights        # 가중치 Decay 실행
├── generate_decay_summary     # 실행 요약 생성
└── check_decay_anomalies      # 이상 패턴 감지
```

### Task 의존성
```
create_decay_logs_table
        ↓
decay_chunk_weights
        ↓
[generate_decay_summary, check_decay_anomalies] (병렬)
```

---

## 🎯 성공 체크리스트

- [ ] Docker Compose 정상 실행
- [ ] Airflow UI 접속 (http://localhost:8080)
- [ ] FourKa DB 연결 테스트 통과
- [ ] `chunk_weight_decay` DAG 활성화
- [ ] 수동 트리거 테스트 성공
- [ ] 로그에서 실행 결과 확인

---

## 📞 문의

- **DAG 설정**: `airflow/dags/ml_weight_decay_dag.py` 파일 확인
- **SQL 로직**: `airflow/dags/sql/decay_chunk_weights.sql` 파일 확인
- **연결 설정**: `docker-compose.airflow.yml`의 환경변수 자동 연결 방식

**🎉 설치 완료! 이제 주간 가중치 Decay 시스템이 자동으로 작동합니다!** 
