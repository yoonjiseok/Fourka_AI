#!/bin/bash
# Airflow 쿠버네티스 배포 스크립트

set -e

# 설정
NAMESPACE="airflow"
RELEASE_NAME="fourka-airflow"

echo "🚀 Airflow 쿠버네티스 배포 시작..."

# 1. Namespace 생성
echo "📦 Namespace 생성 중..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# 2. Secrets 생성
echo "🔐 Secrets 생성 중..."
kubectl apply -f secrets.yaml

# 3. Airflow Helm Repository 추가
echo "📚 Helm Repository 추가 중..."
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# 4. Airflow 설치/업그레이드
echo "⚙️ Airflow 설치 중..."
helm upgrade --install $RELEASE_NAME apache-airflow/airflow \
  --namespace $NAMESPACE \
  --values values.yaml \
  --timeout 10m \
  --wait

# 5. 배포 상태 확인
echo "✅ 배포 상태 확인 중..."
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE

# 6. Webserver URL 출력
echo ""
echo "🌐 Airflow Webserver 접근 방법:"
echo "Port Forward: kubectl port-forward svc/fourka-airflow-webserver 8085:8080 -n $NAMESPACE"
echo "브라우저: http://localhost:8085"
echo "계정: admin / admin"

echo ""
echo "🎉 Airflow 배포 완료!"
