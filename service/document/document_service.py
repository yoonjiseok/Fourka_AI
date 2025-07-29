import os
import google.generativeai as genai
from config import settings
from database.repository.document_repository import DocumentRepository
from fastapi import UploadFile
from service.chunk.chunk_service import ChunkService

class DocumentService:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository
        # 서비스 초기화 시 genai를 설정합니다.
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.embedding_model_name = "gemini-embedding-001"
        self.chunk_service = ChunkService(document_repository)

    async def update_file_name(self, file_id: int, title: str):
        # 파일 제목이라던가 그런거 검증로직 작성
         await self.document_repository.update_file_name(file_id, title)
         

    async def upload_pdf(self, file: UploadFile, title: str, version: str, folder_id: int, commit_message: str):
        print(f"[UPLOAD_PDF] Starting upload for file: {file.filename}")
        
        save_dir = "temp_file_storage"
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file.filename)

        print(f"[UPLOAD_PDF] Saving file to: {save_path}")
        with open(save_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)

        print(f"[UPLOAD_PDF] Creating document record in database")
        doc_id, doc_title, doc_version, doc_created_at = await self.document_repository.create_document(
            title=title,
            version=version,
            folder_id=folder_id,
            commit_message=commit_message
        )

        print(f"[UPLOAD_PDF] Upload completed! Returning response immediately. Background processing will start soon.")
        print(f"[UPLOAD_PDF] Document ID: {doc_id}, Title: {doc_title}")
        
        return doc_id, doc_title, doc_version, doc_created_at, save_path

    async def process_pdf_chunks(self, save_path, doc_id):
        await self.chunk_service.process_pdf_chunks(save_path, doc_id)

    async def get_all_versions(self, folder_id: int):
        return await self.document_repository.get_all_versions_by_folder_id(folder_id)


    async def delete_pdf(self, doc_id: int):
        deleted_doc_id = await self.document_repository.delete_pdf(doc_id)  
        return deleted_doc_id

    async def change_main_document(self, doc_id: int, folder_id: int):
        return await self.document_repository.change_main_document(doc_id, folder_id)
