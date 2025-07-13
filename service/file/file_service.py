from fastapi import File
import fitz
from sqlalchemy.ext.asyncio import AsyncSession

from database.file_repository.repository import FileRepository


def read_file(file: File):
    content = fitz.open(file)
    # 임베딩 시작

class FileService:
    def __init__(self, db: AsyncSession):
        self.file_repository = FileRepository(db)

    async def update_file_name(self, file_id: int, title: str) -> None:
            await self.file_repository.update_file_name(file_id, title)