# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION_NAME: str
    BEDROCK_EMBEDDING_MODEL_ID: str
    BEDROCK_LLM_MODEL_ID: str
    
    # S3 설정 
    S3_BUCKET_NAME: str
    S3_REGION: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_ENDPOINT_URL: str  
    
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

settings = Settings()