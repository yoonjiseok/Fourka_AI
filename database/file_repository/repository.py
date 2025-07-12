from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from database import models


class FileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_file_name(self, doc_id: int, title: str) -> None:
        """
        비동기 방식으로 문서의 제목을 업데이트하고 변경사항을 커밋합니다.
        """
        stmt = (
            update(models.Document)
            .where(models.Document.doc_id == doc_id)
            .values(title=title)
        )

        # 비동기 실행 및 커밋
        await self.db.execute(stmt)
        await self.db.commit()
