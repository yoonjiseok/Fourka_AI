# config.py
from pydantic import MySQLDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    DEBUG: bool = True
    OPENAPI_URL: str | None = "/openapi.json" if DEBUG else None
    API_PREFIX: str = "/api"
    TIMEZONE_LOCATION: str = "Asia/Seoul"
    DB_URL : str

    AWS_ACCESS_KEY_ID: str #.env파일에서 호출
    AWS_SECRET_ACCESS_KEY: str #.env파일에서 호출