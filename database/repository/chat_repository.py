from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select    

from database.models import Chunk, Document, Folder 


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_similar_chunks(self, embedding: list, company_id: int, top_k: int = 5) -> list:
        """
        주어진 임베딩과 가장 유사한 청크를 데이터베이스에서 검색합니다.
        """
        try:
            embedding_str = str(embedding)
            
            query = text("""
            SELECT
                c.chunk_id,                                        
                c.metadata ->> 'content' as content,
                c.metadata ->> 'page_number' as page_number,
                d.title,
                d.doc_id,
                f.name as folder_name,
                c.embedding <=> CAST(:embedding AS vector) AS distance
            FROM chunk c
            JOIN documents d ON c.doc_id = d.doc_id
            JOIN folder f ON d.folder_id = f.folder_id
            WHERE f.company_id = :company_id
            ORDER BY distance
            LIMIT :top_k
            """)
            
            result = await self.db.execute(
            query,
            {
                "embedding": embedding_str,
                "company_id": company_id,    # 이 파라미터가 누락되었음
                "top_k": top_k              # 이 파라미터도 누락되었음
            }
            )
        
            return result.fetchall()  # scalars().unique().all() 대신 fetchall() 사용

            
        except Exception as e:
            print(f"Error in find_similar_chunks: {e}")
            raise
