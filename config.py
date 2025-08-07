# 수정된 config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Bedrock 설정
    BEDROCK_ACCESS_KEY_ID: str
    BEDROCK_SECRET_ACCESS_KEY: str
    BEDROCK_REGION_NAME: str
    BEDROCK_EMBEDDING_MODEL_ID: str
    BEDROCK_LLM_MODEL_ID: str
    GEMINI_API_KEY: str

    #Bedrock guardrail 설정\
    BEDROCK_GUARDRAIL_ID: str
    BEDROCK_GUARDRAIL_VERSION: str

    # S3 설정
    S3_BUCKET_NAME: str
    S3_REGION_NAME: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_ENDPOINT_URL: str
    S3_PROJECT_ID: str  # 카카오클라우드 프로젝트 ID

    API_PREFIX: str

    # FourKa DB 개별 설정
    FOURKA_DB_HOST: str
    FOURKA_DB_PORT: str
    FOURKA_DB_NAME: str
    FOURKA_DB_USER: str
    FOURKA_DB_PASSWORD: str

    # --- 기존 변수들 ---
    DEBUG: bool = True
    TIMEZONE_LOCATION: str = "Asia/Seoul"
    DB_URL: str
    JWT_SECRET: str  # JWT 검증용 시크릿키

    # S3 관련 변수명 통일 (S3_AWS_ 대신 S3_를 사용하는 것으로 가정)
    # S3_AWS_ACCESS_KEY_ID: str -> 이 변수는 삭제합니다.
    # S3_AWS_SECRET_ACCESS_KEY: str -> 이 변수는 삭제합니다.
    # S3_REGION_NAME: str -> S3_REGION과 중복되므로 삭제합니다.

    REDIS_URL: str



settings = Settings()