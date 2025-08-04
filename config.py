# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION_NAME: str
    BEDROCK_EMBEDDING_MODEL_ID: str
    BEDROCK_LLM_MODEL_ID: str

    GEMINI_API_KEY: str  # Gemini API 키
    API_PREFIX: str


    # --- 기존 변수들 ---
    DEBUG: bool = True
    TIMEZONE_LOCATION: str = "Asia/Seoul"
    DB_URL: str
    JWT_SECRET: str  # JWT 검증용 시크릿키

settings = Settings()