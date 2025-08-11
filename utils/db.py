import redis
import redis.asyncio as async_redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
from config import settings  # 설정 파일

# 1. create_async_engine 사용
async_engine = create_async_engine(settings.DB_URL)

# 2. async_sessionmaker 사용
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# 3. async def get_db() 사용
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """비동기 데이터베이스 세션을 생성하는 의존성 함수"""
    async with AsyncSessionLocal() as session:
        yield session



# 동기 Redis 클라이언트 (기존 서비스용)
redis_client = redis.from_url(
    f"{settings.REDIS_URL}",
    decode_responses=True
)

# 비동기 Redis 클라이언트 (스트림용 - 별도 클러스터)
async_redis_client = async_redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True,
    encoding="utf-8"
)