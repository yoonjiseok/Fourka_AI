from database.db import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

from service.file.file_service import FileService


def get_file_service(db: Session = Depends(get_db)) -> FileService:
    return FileService(db)