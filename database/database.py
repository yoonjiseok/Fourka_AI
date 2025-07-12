import os
from fastapi_cloud_cli.config import Settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = Settings().DATABASE_URL

# 비동기 엔진 생성
engine = create_async_engine(DATABASE_URL)

# 비동기 세션 생성기
# autocommit=False, autoflush=False 는 SQLAlchemy의 표준 비동기 설정입니다.
AsyncSessionLocal = async_sessionmaker(engine, autocommit=False, autoflush=False)

