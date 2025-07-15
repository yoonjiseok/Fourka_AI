import os
from database.repository.document_repository import DocumentRepository
from fastapi import UploadFile

class DocumentService:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def update_file_name(self, file_id: int, title: str):
        # 파일 제목이라던가 그런거 검증로직 작성
         doc_id, doc_title = await self.document_repository.update_file_name(file_id, title)
         return doc_id, doc_title
         

    async def upload_pdf(self, file: UploadFile, title: str, version: str, folder_id: int, commit_message: str):
        # temp_file_storage 디렉토리 경로
        save_dir = "temp_file_storage"
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file.filename)

        # 파일 저장 (비동기)
        with open(save_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB씩 읽기
                if not chunk:
                    break
                buffer.write(chunk)

        # DB에 저장
        doc_id, doc_title, doc_version, doc_created_at = await self.document_repository.create_document(
            title=title,
            version=version,
            folder_id=folder_id,
            commit_message=commit_message
        )

        return doc_id, doc_title, doc_version, doc_created_at