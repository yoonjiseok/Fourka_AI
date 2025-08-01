#!/bin/bash

echo "🚀 Apache Airflow 시작 중..."

# 1. Docker Compose로 Airflow 환경 구축
echo "📦 Docker 컨테이너 시작..."
docker-compose -f docker-compose.airflow.yml up -d

# 2. 컨테이너 시작 대기
echo "⏳ Airflow 초기화 대기 중..."
sleep 30

# 3. 상태 확인
echo "🔍 서비스 상태 확인..."
docker-compose -f docker-compose.airflow.yml ps

# 4. 접속 정보 출력
echo ""
echo "✅ Airflow 준비 완료!"
echo ""
echo "📊 Airflow UI: http://localhost:8080"
echo "👤 로그인: admin / admin"
echo ""
echo "📋 다음 단계:"
echo "1. FourKa DB Connection 설정 (아래 중 하나 선택):"
echo "   A) Airflow UI: Admin → Connections → fourka_db 추가"
echo "   B) 환경변수: airflow/env.example을 .env로 복사 후 설정"  
echo "   C) 스크립트: python airflow/connection_setup.py 실행"
echo "2. ml_weight_decay DAG 활성화"
echo "3. 수동 실행 또는 스케줄 대기"
echo ""
echo "🔗 FourKa DB 연결 확인:"
echo "   docker exec airflow_webserver airflow connections test fourka_db"
echo ""

# 5. 로그 확인 명령어 안내
echo "📝 유용한 명령어:"
echo "  로그 확인: docker-compose -f docker-compose.airflow.yml logs -f"
echo "  중지: docker-compose -f docker-compose.airflow.yml down"
echo "" 