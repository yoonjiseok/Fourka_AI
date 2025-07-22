# 의존성 주입 파일
from fastapi import Depends

from database.repository.chat_repository import ChatRepository
from database.repository.document_repository import DocumentRepository
from database.repository.faq_repository import FAQRepository
from database.repository.tag_repository import TagRepository
from dependencies.repository_dependency import get_document_repository, get_faq_repository, get_tag_repository, \
    get_chat_repository
from service.chat.chat_service import ChatService
from service.chunk.chunk_service import ChunkService
from service.document.document_service import DocumentService
from service.faq.faq_service import FAQService
from service.faq.tag_service import TagService


def get_document_service(repo: DocumentRepository = Depends(get_document_repository)) -> DocumentService:
    return DocumentService(repo)

def get_chunk_service(repo: DocumentRepository = Depends(get_document_repository)) -> ChunkService:
    return ChunkService(repo)


def get_faq_service(
    faq_repo: FAQRepository = Depends(get_faq_repository),
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> FAQService:
    return FAQService(faq_repo, tag_repo)

def get_tag_service(tag_repo: TagRepository = Depends(get_tag_repository)) -> TagService:
    return TagService(tag_repo)

def get_chat_service(repo: ChatRepository = Depends(get_chat_repository)) -> ChatService:
    return ChatService(repo)