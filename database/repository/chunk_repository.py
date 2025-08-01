from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Chunk

class ChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_chunk_weights(self, chunk_ids: list):
        """
        주어진 (doc_id, chunk_id) 복합키들의 가중치를 1.1배 증가합니다.
        """
        if not chunk_ids:
            return
            
        # 각 청크를 개별적으로 업데이트
        for doc_id, chunk_id in chunk_ids:
            query = text("""
                UPDATE chunk
                SET weight = weight * 1.1,
                    updated_at = NOW()
                WHERE doc_id = :doc_id AND chunk_id = :chunk_id
            """)
            await self.db.execute(query, {"doc_id": doc_id, "chunk_id": chunk_id})
        await self.db.commit()

    