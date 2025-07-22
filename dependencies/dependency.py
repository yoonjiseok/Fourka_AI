# 의존성 주입 파일
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.document_repository import DocumentRepository
from database.repository.faq_repository import FAQRepository
from database.repository.tag_repository import TagRepository
from service.document.document_service import DocumentService
from service.faq.faq_service import FAQService
from service.faq.tag_service import TagService
from database.repository.chat_repository import ChatRepository
from service.chat.chat_service import ChatService
from utils.db import get_db

def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)

def get_document_service(repo: DocumentRepository = Depends(get_document_repository)) -> DocumentService:
    return DocumentService(repo)


# FAQ 관련 의존성
def get_faq_repository(db: AsyncSession = Depends(get_db)) -> FAQRepository:
    return FAQRepository(db)

def get_tag_repository(db: AsyncSession = Depends(get_db)) -> TagRepository:
    return TagRepository(db)

def get_faq_service(
    faq_repo: FAQRepository = Depends(get_faq_repository),
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> FAQService:
    return FAQService(faq_repo, tag_repo)

def get_tag_service(tag_repo: TagRepository = Depends(get_tag_repository)) -> TagService:
    return TagService(tag_repo)

def get_chat_repository(db: AsyncSession = Depends(get_db)) -> ChatRepository:
    return ChatRepository(db)

def get_chat_service(repo: ChatRepository = Depends(get_chat_repository)) -> ChatService:
    return ChatService(repo)