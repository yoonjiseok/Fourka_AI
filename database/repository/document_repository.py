from sqlalchemy import update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Document

class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_file_name(self, doc_id: int, title: str) -> None:
        """
        비동기 방식으로 문서의 제목을 업데이트합니다.
        """
        # 문서 조회
        document = await self.db.get(Document, doc_id)
        if document:
            # 제목 업데이트
            document.title = title
            await self.db.commit()
            await self.db.refresh(document)
            return document.doc_id, document.title

    async def create_document(self, title: str, version: str, folder_id: int, commit_message: str) -> None:
        """
        새로운 문서를 데이터베이스에 저장합니다.
        """
        from database.models import Document
     
        new_document = Document(
            title=title,
            version=version,
            folder_id=folder_id,
            commit_message=commit_message
        )
        
        self.db.add(new_document)
        await self.db.commit()
        await self.db.refresh(new_document)
        return new_document.doc_id, new_document.title, new_document.version, new_document.created_at