from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_similar_chunks(self, embedding: list, top_k: int = 5) -> list:
        """
        주어진 임베딩과 가장 유사한 청크를 데이터베이스에서 검색합니다.
        """
        # 임베딩 리스트를 pgvector가 인식할 수 있는 문자열 형태로 변환합니다.
        embedding_str = str(embedding)

        query = text("""
            SELECT
                c.metadata ->> 'content' as content,
                c.metadata ->> 'page_number' as page_number,
                d.title,
                c.embedding <=> CAST(:embedding AS vector) AS distance
            FROM chunk c
            JOIN documents d ON c.doc_id = d.doc_id
            ORDER BY distance
            LIMIT :top_k
        """)

        result = await self.db.execute(
            query,

            {"embedding": embedding_str, "top_k": top_k}
        )
        return result.fetchall()
