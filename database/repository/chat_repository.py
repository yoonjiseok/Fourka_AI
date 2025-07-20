from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector
import numpy as np

class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_similar_chunks(self, embedding: list, top_k: int = 5) -> list:
        """
        주어진 임베딩과 가장 유사한 청크를 데이터베이스에서 검색합니다.
        """
        # pgvector의 l2_distance 연산자를 사용하여 유사도 검색
        query = text(f"""
            SELECT
                c.metadata_ ->> 'content' as content,
                c.metadata_ ->> 'page_number' as page_number,
                d.title,
                c.embedding <-> CAST(:embedding AS vector) AS distance
            FROM chunk c
            JOIN documents d ON c.doc_id = d.doc_id
            ORDER BY distance
            LIMIT :top_k
        """)

        result = await self.db.execute(
            query,
            {"embedding": np.array(embedding), "top_k": top_k}
        )
        return result.fetchall()