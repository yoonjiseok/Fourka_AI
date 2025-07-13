from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from service.file.file_service import FileService


def get_file_service(db: AsyncSession = Depends(get_db)) -> FileService:
    return FileService(db)