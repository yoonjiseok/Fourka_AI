import asyncio
import boto3 
import json 
from unstructured.chunking.title import chunk_by_title
from unstructured.partition.auto import partition

from config import settings
from database.repository.document_repository import DocumentRepository
from utils.chunk_postprocess import merge_incomplete_chunks, validate_chunk_quality, add_overlap_to_chunks, clean_text


class ChunkService:
    def __init__(self, document_repository: DocumentRepository, bedrock_runtime, embedding_model_id: str):
        self.document_repository = document_repository
        self.bedrock_runtime = bedrock_runtime
        self.embedding_model_id = embedding_model_id

    async def process_pdf_chunks(self, save_path, doc_id):
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
        
        print(f"[BACKGROUND_TASK] Step 3: Processing and saving {len(chunks)} chunks...")
        for idx, chunk in enumerate(chunks):
            cleaned_content = clean_text(chunk.text)
            
            # 텍스트를 임베딩으로 변환 (boto3는 동기 라이브러리이므로 기존처럼 별도 스레드에서 실행)
            embedding = await loop.run_in_executor(
                None,
                self._text_to_embedding,
                cleaned_content
            )
            
            meta = chunk.metadata.to_dict()
            simplified_meta = {
                'filename': meta.get('filename', ''),
                'page_number': meta.get('page_number', 1),
                'content': cleaned_content
            }

            # DB에 청크 저장
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
        텍스트를 AWS Bedrock의 Titan 모델을 사용하여 벡터로 변환합니다.
        """

        try:
            body = json.dumps({"inputText": text})
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.embedding_model_id,
                accept="application/json",
                contentType="application/json"
            )
            response_body = json.loads(response.get("body").read())
            return response_body.get("embedding")
        except Exception as e:
            print(f"Error creating embedding with Bedrock Titan: {e}")
            raise