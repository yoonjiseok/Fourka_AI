from sqlalchemy import update, insert, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Document, Chunk

class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_file_name(self, doc_id: int, title: str) -> None:
        """
        비동기 방식으로 문서의 제목을 업데이트합니다.
        """
        # 문서 조회
        document = await self.db.get(Document, doc_id)
        if document:
            # 제목 업데이트
            document.title = title
            await self.db.commit()
            await self.db.refresh(document)
            return document.doc_id, document.title

    async def create_document(self, title: str, version: str, folder_id: int, commit_message: str) -> None:
        """
        새로운 문서를 데이터베이스에 저장합니다.
        """
     
        new_document = Document(
            title=title,
            version=version,
            folder_id=folder_id,
            commit_message=commit_message
        )
        
        self.db.add(new_document)
        await self.db.commit()
        await self.db.refresh(new_document)
        return new_document.doc_id, new_document.title, new_document.version, new_document.created_at

    async def create_chunk(self, doc_id: int, embedding: list, metadata: dict):
        """
        비동기 방식으로 청크를 데이터베이스에 저장합니다.
        문서별로 chunk_id를 1부터 증가시키면서 저장합니다.
        """
        # 해당 문서의 최대 chunk_id 조회
        max_chunk_id_query = select(func.max(Chunk.chunk_id)).where(Chunk.doc_id == doc_id)
        result = await self.db.execute(max_chunk_id_query)
        max_chunk_id = result.scalar()
        
        # 새로운 chunk_id 계산 (없으면 1부터 시작)
        new_chunk_id = (max_chunk_id or 0) + 1
        
        # 새로운 청크 생성
        new_chunk = Chunk(
            chunk_id=new_chunk_id,
            doc_id=doc_id,
            embedding=embedding,
            metadata_=metadata
        )
        
        self.db.add(new_chunk)
        await self.db.commit()
        await self.db.refresh(new_chunk)
        
        # 저장 후 embedding 확인
        print(f"Saved chunk: chunk_id={new_chunk.chunk_id}, doc_id={new_chunk.doc_id}")
        if new_chunk.embedding is not None:
            embedding_sample = new_chunk.embedding[:5] if hasattr(new_chunk.embedding, '__getitem__') else 'Not iterable'
            print(f"Embedding after save: {embedding_sample}")
        else:
            print("Embedding after save: None")
        
        return new_chunk
        
