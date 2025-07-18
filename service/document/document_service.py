import asyncio
import numpy as np
import os
from fastapi import UploadFile
from google import genai
from sklearn.decomposition import PCA
from unstructured.chunking.title import chunk_by_title
from unstructured.partition.auto import partition

from config import settings
from database.repository.document_repository import DocumentRepository
from service.document.modify_service import compare_text
from utils.chunk_postprocess import merge_incomplete_chunks, validate_chunk_quality, add_overlap_to_chunks, clean_text


class DocumentService:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def update_file_name(self, file_id: int, title: str):
        # 파일 제목이라던가 그런거 검증로직 작성
         await self.document_repository.update_file_name(file_id, title)
         

    async def upload_pdf(self, file: UploadFile, title: str, version: str, folder_id: int, commit_message: str):
        print(f"[UPLOAD_PDF] Starting upload for file: {file.filename}")
        
        # temp_file_storage 디렉토리 경로
        save_dir = "temp_file_storage"
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file.filename)

        # 파일 저장 (비동기)
        print(f"[UPLOAD_PDF] Saving file to: {save_path}")
        with open(save_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB씩 읽기
                if not chunk:
                    break
                buffer.write(chunk)

        # DB에 문서 정보 저장
        print(f"[UPLOAD_PDF] Creating document record in database")
        doc_id, doc_title, doc_version, doc_created_at = await self.document_repository.create_document(
            title=title,
            version=version,
            folder_id=folder_id,
            commit_message=commit_message
        )

        print(f"[UPLOAD_PDF] Upload completed! Returning response immediately. Background processing will start soon.")
        print(f"[UPLOAD_PDF] Document ID: {doc_id}, Title: {doc_title}")
        
        # 청크 분석 및 저장은 백그라운드에서 처리
        return doc_id, doc_title, doc_version, doc_created_at, save_path

    async def process_pdf_chunks(self, save_path, title, version, folder_id, commit_message, doc_id):
        print(f"[BACKGROUND_TASK] Starting background chunk processing for doc_id: {doc_id}")
        print(f"[BACKGROUND_TASK] Processing file: {save_path}")
        
        # 이벤트 루프와 executor 가져오기
        loop = asyncio.get_event_loop()
        
        # CPU 집약적 작업들을 별도 스레드에서 실행
        print(f"[BACKGROUND_TASK] Step 1: Partitioning PDF (in separate thread)...")
        elements = await loop.run_in_executor(None, partition, save_path)
        
        print(f"[BACKGROUND_TASK] Step 2: Chunking by title (in separate thread)...")
        chunks = await loop.run_in_executor(
            None, 
            self._chunk_processing_sync,
            elements
        )
        
        # 1단계: 모든 청크의 텍스트를 임베딩으로 변환 (배치 수집)
        chunk_data = []
        embeddings = []
        
        print(f"[BACKGROUND_TASK] Step 3: Processing {len(chunks)} chunks for embeddings...")
        for idx, chunk in enumerate(chunks):
            cleaned_content = clean_text(chunk.text)
            meta = chunk.metadata.to_dict()
            
            # 필요한 정보만 남기기
            simplified_meta = {
                'filename': meta.get('filename', ''),
                'page_number': meta.get('page_number', 1),
                'file_directory': meta.get('file_directory', 'temp_file_storage')
            }
            
            # 텍스트를 임베딩으로 변환 (별도 스레드에서 실행)
            embedding = await loop.run_in_executor(
                None,
                self._text_to_embedding,
                cleaned_content
            )
            
            chunk_data.append({
                'content': cleaned_content,
                'metadata': simplified_meta,
                'original_embedding': embedding
            })
            embeddings.append(embedding)
            
            print(f"[BACKGROUND_TASK] Generated embedding for chunk {idx + 1}/{len(chunks)}")

        # 2단계: 배치로 PCA 차원 축소 적용 (별도 스레드에서 실행)
        print("[BACKGROUND_TASK] Step 4: Applying batch PCA dimension reduction (in separate thread)...")
        reduced_embeddings = await loop.run_in_executor(
            None,
            self._batch_reduce_embeddings,
            embeddings
        )
        
        # 3단계: 축소된 임베딩을 DB에 저장
        print(f"[BACKGROUND_TASK] Step 5: Saving {len(reduced_embeddings)} chunks to database...")
        for i, (chunk_info, reduced_embedding) in enumerate(zip(chunk_data, reduced_embeddings)):
            await self.document_repository.create_chunk(
                doc_id=doc_id,
                embedding=reduced_embedding,
                metadata=chunk_info['metadata']
            )
            print(f"[BACKGROUND_TASK] Saved chunk {i + 1}/{len(chunks)} to database")
        
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
        텍스트를 임베딩 벡터로 변환합니다.
        Google AI의 임베딩 모델을 사용합니다.
        """
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        embedding = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text
        )
    
        # ContentEmbedding 객체에서 벡터 값 추출
        embedding_values = embedding.embeddings[0].values
        return embedding_values
    
    def _batch_reduce_embeddings(self, embeddings: list) -> list:
        """
        배치로 임베딩 차원을 3072에서 1536으로 축소합니다.
        여러 샘플에 대해 한 번에 PCA를 적용합니다.
        """
        n_samples = len(embeddings)
        n_features = len(embeddings[0]) if embeddings else 0
        target_dimensions = 1536
        
        # 샘플 수가 부족한 경우의 처리
        if n_samples < 2:
            print("Warning: PCA requires at least 2 samples. Using original embeddings.")
            return embeddings
        elif n_samples <= target_dimensions:
            # 샘플 수가 목표 차원보다 적은 경우: 가능한 최대 차원으로 축소 후 패딩
            print(f"Sample count ({n_samples}) is less than target dimensions ({target_dimensions})")
            print("Using maximum possible PCA dimensions and padding with zeros")
            
            embeddings_array = np.array(embeddings)
            max_components = min(n_samples - 1, n_features)
            
            # PCA로 최대 가능한 차원으로 축소
            pca = PCA(n_components=max_components)
            reduced_array = pca.fit_transform(embeddings_array)
            
            # 1536차원까지 0으로 패딩
            padding_size = target_dimensions - max_components
            padding = np.zeros((n_samples, padding_size))
            padded_array = np.hstack([reduced_array, padding])
            
            explained_variance_ratio = np.sum(pca.explained_variance_ratio_)
            print(f"PCA dimensions: {max_components}, Padded to: {target_dimensions}")
            print(f"Explained variance ratio: {explained_variance_ratio:.4f}")
            
            return padded_array.tolist()
        else:
            # 샘플 수가 충분한 경우: 정확히 1536차원으로 축소
            embeddings_array = np.array(embeddings)
            print(f"Embeddings array shape: {embeddings_array.shape}")
            print(f"Reducing dimensions: {n_features} -> {target_dimensions}")
            
            pca = PCA(n_components=target_dimensions)
            reduced_array = pca.fit_transform(embeddings_array)
            
            explained_variance_ratio = np.sum(pca.explained_variance_ratio_)
            print(f"Explained variance ratio: {explained_variance_ratio:.4f}")
            
            return reduced_array.tolist()


    async def get_all_versions(self, folder_id: int):
        return await self.document_repository.get_all_versions_by_folder_id(folder_id)

    async def compare_two_docs(self, doc_id: int) -> str:
        """
        :param doc_id: 비교할 문서의 ID
        :return: 두 문서의 다른점

        TODO: S3 URL이 아직 활성화되지 않은 관계로 주석 처리해놓겠습니다. 그래서 아직 진짜 잘 되는지 수 없음...이런식으로 출력될 것이다 까지로만 봐주시면 될 것 같아요.
        """
        # using_doc_id = await self.document_repository.get_using_doc_id()
        # main_url = await self.document_repository.get_s3_url(using_doc_id)
        # compare_url = await self.document_repository.get_s3_url(doc_id)
        # main_pdf = download_file_to_memory(main_url)
        # compare_pdf = download_file_to_memory(compare_url)
        # text = compare_text(extract_text_from_pdf(main_pdf), extract_text_from_pdf(compare_pdf))
        main_pdf = ("""원본 사내 규정 (예시) \n제 1 장 총칙\n제 1 조 (목적) 이 규정은 주식회사 ABC (이하 "회사"라 한다)의 조직 구성원의 기본적인 근무 조건과 복무 규율을 정함을 목적으로 한다.\n제 2 조 (적용 범위) 이 규정은 회사에 소속된 모든 임직원에게 적용된다.\n제 2 장 근무 시간\n제 3 조 (근무 시간) 회사의 통상 근무 시간은 주 5일, 1일 8시간으로 한다. 단, 업무의 특성에 따라 변경될 수 있다.\n제 4 조 (휴게 시간) 근무 시간 중 1시간의 휴게 시간을 부여한다. 휴게 시간은 자유롭게 사용할 수 있다.""")
        compare_pdf = """수정된 사내 규정 (예시)\n\n제 1 장 총칙\n제 1 조 (목적) 이 규정은 주식회사 ABC (이하 "회사"라고 칭한다)의 조직 구성원의 기본적인 근무 조건, 복무 규율 및 윤리 기준을 명확히 하여 효율적인 업무 수행을 도모함을 그 목적으로 한다.\n제 2 조 (적용 범위) 이 규정은 회사에 소속된 모든 임원 및 직원을 포함한 모든 구성원에게 적용된다.\n제 2 장 근무 시간 및 휴게\n\n제 3 조 (근무 시간) 회사의 기본적인 근무 시간은 주 5일, 1일 8시간을 원칙으로 한다. 다만, 업무의 성격이나 필요에 따라 근무 시간 및 형태가 변경될 수 있다.\n제 4 조 (휴게 시간) 근무 중에는 총 1시간의 휴게 시간이 주어진다. 휴게 시간의 사용은 원칙적으로 자유롭게 하되, 업무에 지장을 초래하지 않도록 한다."""
        text = compare_text(main_pdf, compare_pdf)
        print(text)
        return text