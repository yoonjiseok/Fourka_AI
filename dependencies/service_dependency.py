# 의존성 주입 파일
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.chat_repository import ChatRepository
from database.repository.chunk_repository import ChunkRepository
from database.repository.company_repository import CompanyRepository
from database.repository.document_repository import DocumentRepository
from database.repository.tag_repository import TagRepository
from database.repository.feedback_repository import FeedbackRepository
from database.repository.folder_repository import FolderRepository
from dependencies.repository_dependency import get_document_repository, get_faq_repository, get_tag_repository, \
    get_chat_repository, get_chunk_repository, get_feedback_repository, get_folder_repository, get_redis_service
from service.chat.chat_service import ChatService
from service.chunk.chunk_service import ChunkService
from service.document.document_service import DocumentService
from service.faq.faq_service import FAQService
from service.faq.tag_service import TagService
from service.folder.folder_service import FolderService
from service.redis.redis_service import RedisService
from utils.db import get_db 

from service.feedback.feedback_service import FeedbackService
from database.repository.keyword_repository import KeywordRepository


def get_document_service(repo: DocumentRepository = Depends(get_document_repository),redis: RedisService = Depends(get_redis_service)) -> DocumentService:
    return DocumentService(repo, redis_service=redis)

def get_chunk_service(repo: DocumentRepository = Depends(get_document_repository)) -> ChunkService:
    return ChunkService(repo)


def get_faq_service(db_session: AsyncSession = Depends(get_db)) -> FAQService:
    return FAQService(db_session=db_session)

def get_tag_service(tag_repo: TagRepository = Depends(get_tag_repository)) -> TagService:
    return TagService(tag_repo)

def get_feedback_service(
    feedback_repo: FeedbackRepository = Depends(get_feedback_repository),
    chunk_repo: ChunkRepository = Depends(get_chunk_repository),
    chat_repo: ChatRepository = Depends(get_chat_repository)
) -> FeedbackService:
    return FeedbackService(feedback_repo, chunk_repo, chat_repo)

def get_folder_service(folder_repo: FolderRepository = Depends(get_folder_repository),docu_repo: DocumentRepository = Depends(get_document_repository)) -> FolderService:
    return FolderService(folder_repository=folder_repo, document_repository=docu_repo)

def get_chat_service(db: AsyncSession = Depends(get_db)):
    chat_repo = ChatRepository(db)
    company_repo = CompanyRepository(db)
    keyword_repo = KeywordRepository(db) 
    
    return ChatService(
        chat_repository=chat_repo,
        company_repository=company_repo,
        keyword_repository=keyword_repo
    )