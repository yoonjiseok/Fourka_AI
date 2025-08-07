# =========================================
# 1. Build Stage: 컴파일 및 의존성 설치
# =========================================
FROM python:3.10-slim as builder

# 빌드에 필요한 시스템 라이브러리 설치 (-dev 포함)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic-dev \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# =========================================
# 2. Final Stage: 실제 운영(배포) 환경
# =========================================
FROM python:3.10-slim

# "실행"에 필요한 시스템 라이브러리만 설치 (-dev 같은 빌드용 패키지는 제외)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Build Stage에서 설치한 파이썬 패키지 복사
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# [수정] Build Stage에서 설치한 실행 파일들도 복사
COPY --from=builder /usr/local/bin /usr/local/bin

# 소스 코드 복사
COPY . .

# 데이터 디렉토리 생성
RUN mkdir -p /app/chroma_db

# [추가] 보안 강화를 위해 non-root 유저로 실행
# 새로운 사용자를 만들고, 앱 디렉토리의 소유권을 부여합니다.
RUN useradd --create-home appuser
RUN chown -R appuser:appuser /app
# 이후 명령은 appuser 권한으로 실행됩니다.
USER appuser

# FastAPI 앱 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]