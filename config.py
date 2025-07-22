# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    DEBUG: bool = True
    OPENAPI_URL: str | None = "/openapi.json" if DEBUG else None
    API_PREFIX: str = "/api"
    TIMEZONE_LOCATION: str = "Asia/Seoul"
    DB_URL : str
    GEMINI_API_KEY : str | None = None
    JWT_SECRET: str  # JWT 검증용 시크릿키

settings = Settings()