FROM apache/airflow:2.7.0

# (선택) 아주 소량의 OS 유틸만
USER airflow

# 필요한 provider만 설치 (용량 최소)
RUN pip install --no-cache-dir apache-airflow-providers-postgres==5.8.0

# DAG/SQL을 이미지에 내장 (경로는 compose/k8s 모두 동일하게)
COPY dags /opt/airflow/dags
# 예: ./airflow/dags/sql/decay_chunk_weights.sql → /opt/airflow/dags/sql/decay_chunk_weights.sql
