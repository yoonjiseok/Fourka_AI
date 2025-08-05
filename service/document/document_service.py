import os
import boto3  # << 변경: boto3 import
from database.repository.document_repository import DocumentRepository
from fastapi import UploadFile

from exception.models.exception import DocumentException
from service.chunk.chunk_service import ChunkService
from utils.s3_service import S3Service
from config import settings # << 변경: settings import 추가

class DocumentService:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository
        
        # S3 서비스 초기화
        try:
            self.s3_service = S3Service()
        except Exception as e:
            raise DocumentException(message=f"S3 서비스 초기화 실패: {e}")

        # Bedrock 클라이언트 초기화
        try:
            self.bedrock_runtime = boto3.client(
                service_name="bedrock-runtime",
                region_name=settings.AWS_REGION_NAME,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            self.embedding_model_id = settings.BEDROCK_EMBEDDING_MODEL_ID

        except Exception as e:
            raise DocumentException(message=f"AWS Bedrock 클라이언트 초기화 실패: {e}")

        # ChunkService에 Bedrock 클라이언트와 모델 ID를 전달
        self.chunk_service = ChunkService(
            document_repository=document_repository,
            bedrock_runtime=self.bedrock_runtime,
            embedding_model_id=self.embedding_model_id
        )


    async def update_file_name(self, file_id: int, title: str):
        # 파일 제목이라던가 그런거 검증로직 작성
         await self.document_repository.update_file_name(file_id, title)
         

    async def upload_pdf(self, file: UploadFile, title: str, version: str, folder_id: int, commit_message: str):
        print(f"[UPLOAD_PDF] Starting upload for file: {file.filename}")
        
        try:
            # S3에 파일 업로드
            print(f"[UPLOAD_PDF] Uploading file to S3...")
            s3_url = await self.s3_service.upload_file(file, folder_name="documents")
            print(f"[UPLOAD_PDF] S3 upload completed. URL: {s3_url}")
            
            # 임시 로컬 파일도 저장 (청크 처리를 위해)
            save_dir = "temp_file_storage"
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, file.filename)

            print(f"[UPLOAD_PDF] Saving temporary file to: {save_path}")
            await file.seek(0)  # 파일 포인터를 처음으로 이동
            with open(save_path, "wb") as buffer:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    buffer.write(chunk)

            print(f"[UPLOAD_PDF] Creating document record in database with S3 URL")
            doc_id, doc_title, doc_version, doc_created_at = await self.document_repository.create_document(
                title=title,
                version=version,
                folder_id=folder_id,
                commit_message=commit_message,
                url=s3_url  # S3 URL 저장
            )

            print(f"[UPLOAD_PDF] Upload completed! Document ID: {doc_id}, S3 URL: {s3_url}")
            
            return doc_id, doc_title, doc_version, doc_created_at, save_path
            
        except Exception as e:
            print(f"[UPLOAD_PDF] Error during upload: {e}")
            raise DocumentException(message=f"파일 업로드 실패: {e}")

    async def process_pdf_chunks(self, save_path, doc_id):
        try:
            await self.chunk_service.process_pdf_chunks(save_path, doc_id)
            print(f"[PROCESS_CHUNKS] Chunk processing completed for doc_id: {doc_id}")
        except Exception as e:
            print(f"[PROCESS_CHUNKS] Error during chunk processing: {e}")
        finally:
            # 임시 파일 정리
            try:
                if os.path.exists(save_path):
                    os.remove(save_path)
                    print(f"[PROCESS_CHUNKS] Temporary file removed: {save_path}")
            except Exception as e:
                print(f"[PROCESS_CHUNKS] Error removing temporary file: {e}")

    async def get_all_versions(self, folder_id: int):
        return await self.document_repository.get_all_versions_by_folder_id(folder_id)


    async def delete_pdf(self, doc_id: int):
        try:
            # 문서 정보 조회 (S3 URL 가져오기)
            document = await self.document_repository.get_document_by_id(doc_id)
            
            # DB에서 문서 삭제
            deleted_doc_id = await self.document_repository.delete_pdf(doc_id)
            
            # S3에서 파일 삭제 (URL이 있는 경우)
            if document and document.url:
                try:
                    success = self.s3_service.delete_file(document.url)
                    if success:
                        print(f"[DELETE_PDF] S3 file deleted successfully: {document.url}")
                    else:
                        print(f"[DELETE_PDF] Failed to delete S3 file: {document.url}")
                except Exception as e:
                    print(f"[DELETE_PDF] Error deleting S3 file: {e}")
            
            return deleted_doc_id
            
        except Exception as e:
            print(f"[DELETE_PDF] Error during document deletion: {e}")
            raise DocumentException(message=f"문서 삭제 실패: {e}")

    async def change_main_document(self, doc_id: int, folder_id: int):
        return await self.document_repository.change_main_document(doc_id, folder_id)