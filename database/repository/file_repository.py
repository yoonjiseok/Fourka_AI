from typing import Sequence

from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Document

class FileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_file_name(self, doc_id: int, title: str) -> None:
        from database.models import Document
        stmt = (
            update(Document)
            .where(Document.doc_id == doc_id)
            .values(title=title)
        )

        await self.db.execute(stmt)
        await self.db.commit()

    async def get_all_versions_by_folder_id(self, folder_id: int) -> Sequence[Document]:
        stmt = (
            select(Document)
            .where(Document.doc_folder_id==folder_id)
            .order_by(Document.created_at)
        )

        result = await self.db.execute(stmt)
        documents: Sequence[Document] = result.scalars().all()
        return documents