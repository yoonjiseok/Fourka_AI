import os
import asyncio
from database.repository.document_repository import DocumentRepository
from fastapi import UploadFile
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from utils.chunk_postprocess import merge_incomplete_chunks, validate_chunk_quality, add_overlap_to_chunks, clean_text
import google.generativeai as genai
from config import settings

# PCA와 numpy는 더 이상 필요하지 않으므로 삭제합니다.
# from sklearn.decomposition import PCA
# import numpy as np

class DocumentService:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository
        # 서비스 초기화 시 genai를 설정합니다.
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.embedding_model_name = "models/embedding-001"

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

    async def process_pdf_chunks(self, save_path, title, version, folder_id, commit_message, doc_id):
        print(f"[BACKGROUND_TASK] Starting background chunk processing for doc_id: {doc_id}")
        print(f"[BACKGROUND_TASK] Processing file: {save_path}")
        
        loop = asyncio.get_event_loop()
        
        print(f"[BACKGROUND_TASK] Step 1: Partitioning PDF (in separate thread)...")
        elements = await loop.run_in_executor(None, partition, save_path)
        
        print(f"[BACKGROUND_TASK] Step 2: Chunking by title (in separate thread)...")
        chunks = await loop.run_in_executor(
            None, 
            self._chunk_processing_sync,
            elements
        )
        
        # Step 3: 각 청크를 처리하고 바로 DB에 저장 (PCA 로직 제거)
        print(f"[BACKGROUND_TASK] Step 3: Processing and saving {len(chunks)} chunks...")
        for idx, chunk in enumerate(chunks):
            cleaned_content = clean_text(chunk.text)
            
            # 텍스트를 768차원 임베딩으로 변환 (별도 스레드에서 실행)
            embedding = await loop.run_in_executor(
                None,
                self._text_to_embedding,
                cleaned_content
            )
            
            # 메타데이터 준비 (검색 결과를 위해 content 추가)
            meta = chunk.metadata.to_dict()
            simplified_meta = {
                'filename': meta.get('filename', ''),
                'page_number': meta.get('page_number', 1),
                'content': cleaned_content
            }

            # DB에 768차원 청크 저장
            await self.document_repository.create_chunk(
                doc_id=doc_id,
                embedding=embedding,
                metadata=simplified_meta
            )
            print(f"[BACKGROUND_TASK] Saved chunk {idx + 1}/{len(chunks)} to database")
        
        print(f"[BACKGROUND_TASK] ✅ Background processing completed for doc_id: {doc_id}")
        print(f"[BACKGROUND_TASK] Total chunks processed: {len(chunks)}")
    
    def _chunk_processing_sync(self, elements):
        """
        동기 청킹 작업을 별도 함수로 분리
        """
        chunks = chunk_by_title(
            elements,
            combine_text_under_n_chars=800,
            new_after_n_chars=3000,
            max_characters=6000
        )
        chunks = merge_incomplete_chunks(chunks)
        chunks = validate_chunk_quality(chunks)
        chunks = add_overlap_to_chunks(chunks, overlap_chars=200)
        return chunks
    
    def _text_to_embedding(self, text: str) -> list:
        """
        텍스트를 Google의 'embedding-001' 모델을 사용하여 768차원 벡터로 변환합니다.
        """
        result = genai.embed_content(
            model=self.embedding_model_name,
            content=text,
            task_type="retrieval_document"  # 문서를 저장할 때는 이 타입을 사용
        )
        return result['embedding']
    
    # _batch_reduce_embeddings 메소드는 더 이상 필요 없으므로 삭제합니다.

