# 의존성 주입 파일
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from utils.db import get_db
from database.repository.document_repository import DocumentRepository
from service.document.document_service import DocumentService

def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)

def get_document_service(repo: DocumentRepository = Depends(get_document_repository)) -> DocumentService:
    return DocumentService(repo)


"""
# 만약 chat_repository와 서비스를 따로 만든다면
def get_chat_repository(db: AsyncSession = Depends(get_db)) -> chatRepository:
    return chatRepository(db)

def get_chat_service(repo: chatRepository = Depends(get_chat_repository)) -> chatService:
    return chatService(repo)
    
작성후 

컨트롤러의 Depends에 해당 함수들을 추가로 작성하면 됨
만약 서비스 계층에서 두개의 레포지토리를 사용해야한다면
__init__에서 Repository를 주입받으면 됨
"""