# 의존성 주입 파일
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository.chat_repository import ChatRepository
from database.repository.chunk_repository import ChunkRepository
from database.repository.document_repository import DocumentRepository
from database.repository.faq_repository import FAQRepository
from database.repository.tag_repository import TagRepository
from database.repository.feedback_repository import FeedbackRepository
from database.repository.folder_repository import FolderRepository
from service.redis.redis_service import RedisService
from utils.db import get_db, redis_client


def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)

# FAQ 관련 의존성
def get_faq_repository(db: AsyncSession = Depends(get_db)) -> FAQRepository:
    return FAQRepository(db)

def get_tag_repository(db: AsyncSession = Depends(get_db)) -> TagRepository:
    return TagRepository(db)

def get_chat_repository(db: AsyncSession = Depends(get_db)) -> ChatRepository:
    return ChatRepository(db)

def get_chunk_repository(db: AsyncSession = Depends(get_db)) -> ChunkRepository:
    return ChunkRepository(db)

def get_feedback_repository(db: AsyncSession = Depends(get_db)) -> FeedbackRepository:
    return FeedbackRepository(db)

def get_folder_repository(db: AsyncSession = Depends(get_db)) -> FolderRepository: # 추가
    return FolderRepository(db)

def get_redis_service() -> RedisService:
    """RedisService 인스턴스를 생성하는 의존성 함수"""
    return RedisService(redis_client=redis_client)

