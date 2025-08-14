# =========================================
# 1. Build Stage: 컴파일 및 의존성 설치
# =========================================
FROM python:3.10-slim-bullseye AS builder

# 빌드에 '만' 필요한 시스템 라이브러리 설치
# build-essential: C/C++ 코드를 컴파일하는 데 필요
# libmagic-dev: python-magic 라이브러리 설치에 필요
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# pip를 먼저 업그레이드하고 requirements.txt를 복사하여 캐시 효율 극대화
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# =========================================
# 2. Final Stage
# =========================================
FROM python:3.10-slim-bullseye

# "실행"에 필요한 시스템 라이브러리 설치 (Java는 JRE 17 그대로 사용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 보안 강화를 위해 non-root 유저 먼저 생성
RUN useradd --create-home appuser

# Build Stage에서 설치한 파이썬 패키지 복사
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 소스 코드 복사
COPY . .

# 데이터 디렉토리 생성 및 소유권 변경
# RUN mkdir -p /app/chroma_db # COPY 시 . 이 포함되어 있다면 필요 없을 수 있음
RUN chown -R appuser:appuser /app

# 이후 명령은 appuser 권한으로 실행
USER appuser

# FastAPI 앱 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]