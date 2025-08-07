import boto3  # << 변경: boto3 import
import difflib
import fitz
import io
import os
from fastapi import UploadFile

from config import settings
from database.repository.document_repository import DocumentRepository
from exception.models.exception import DocumentException
from service.chunk.chunk_service import ChunkService
from service.redis.redis_service import RedisService
from utils import s3_utils
from utils.s3_service import S3Service
from utils.s3_utils import extract_text_from_pdf, compare_text


class DocumentService:
    def __init__(self, document_repository: DocumentRepository, redis_service: RedisService):
        self.document_repository = document_repository

        # S3 서비스 초기화
        try:
            self.s3_service = S3Service()
        except Exception as e:
            raise DocumentException(message=f"S3 서비스 초기화 실패: {e}")
        self.redis_service = redis_service

        # Bedrock 클라이언트 초기화
        try:
            self.bedrock_runtime = boto3.client(
                service_name="bedrock-runtime",
                region_name=settings.BEDROCK_REGION_NAME,
                aws_access_key_id=settings.BEDROCK_ACCESS_KEY_ID,
                aws_secret_access_key=settings.BEDROCK_SECRET_ACCESS_KEY
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

    def compare_text(text1: str, text2: str) -> str:
        """두 텍스트의 차이를 비교하는 헬퍼 함수"""
        differ = difflib.Differ()
        diff = differ.compare(text1.splitlines(), text2.splitlines())
        changed_lines = [line for line in diff if line.startswith('+ ') or line.startswith('- ')]
        return '\n'.join(changed_lines)

    def extract_text_from_pdf(pdf_stream: io.BytesIO) -> str:
        """PDF 메모리 스트림에서 텍스트를 추출합니다."""
        full_text = ""
        try:
            with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
                for page in doc:
                    full_text += page.get_text()
            print("텍스트 추출 성공.")
            return full_text
        except Exception as e:
            print(f"PDF 처리 중 오류 발생: {e}")
            return ""

    async def compare_two_docs(self, doc_id: int, folder_id: int) -> str:
        """
        S3에서 문서를 가져와 비교하고, Redis 캐시를 활용합니다.
        """
        # 1. 기준 문서와 비교 대상 문서의 ID를 가져옵니다.
        using_doc_id = await self.document_repository.get_using_doc_id(folder_id=folder_id)
        if not using_doc_id:
            raise ValueError("기준이 되는 문서를 찾을 수 없습니다.")

        # 2. Redis 캐시를 확인합니다.
        cached_result = self.redis_service.get_comparison(main_doc_id=using_doc_id, compare_doc_id=doc_id)
        if cached_result:
            print(f"캐시 히트! Redis에서 결과를 반환합니다: comparison:{using_doc_id}:{doc_id}")
            return cached_result['diff_result']

        print(f"캐시 미스. 문서 비교를 시작합니다: comparison:{using_doc_id}:{doc_id}")

        # 3. DB에서 각 문서의 S3 URL을 가져옵니다.
        main_url = await self.document_repository.get_s3_url(using_doc_id)
        compare_url = await self.document_repository.get_s3_url(doc_id)

        if not main_url or not compare_url:
            raise FileNotFoundError("하나 이상의 문서 URL을 DB에서 찾을 수 없습니다.")

        # 4. S3에서 PDF 파일을 다운로드합니다.
        main_pdf_stream = s3_utils.download_file_from_s3(main_url)
        compare_pdf_stream = s3_utils.download_file_from_s3(compare_url)

        if not main_pdf_stream or not compare_pdf_stream:
            raise ConnectionError("S3에서 하나 이상의 파일을 다운로드하는 데 실패했습니다.")

        # 5. PDF에서 텍스트를 추출합니다.
        main_text = extract_text_from_pdf(main_pdf_stream)
        compare_text_content = extract_text_from_pdf(compare_pdf_stream)

        main_pdf_stream.close()
        compare_pdf_stream.close()

        # 6. 텍스트 차이를 계산합니다.
        diff_result = compare_text(main_text, compare_text_content)

        # 7. 새로운 비교 결과를 Redis에 저장합니다.
        self.redis_service.save_comparison(
            main_doc_id=using_doc_id,
            compare_doc_id=doc_id,
            main_text=main_text,
            compare_text=compare_text_content,
            diff_result=diff_result
        )
        print("새로운 비교 결과를 Redis에 저장했습니다.")

        return diff_result