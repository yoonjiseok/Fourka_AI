from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Chat
from database.models import ChatType

class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def save_chat(self, question: str, chat_type: ChatType, chat_room_id: int, user_id: int, chunk_ids: list) -> int:
        """채팅 메시지를 안정적으로 저장하고 생성된 ID를 반환합니다."""
        print(f"DEBUG: Saving chat for chat_room_id: {chat_room_id}")
        chat = Chat(
            question=question,
            chat_type=chat_type,
            chat_room_id=chat_room_id,
            user_id=user_id,
            chunk_ids=chunk_ids
        )
        self.db.add(chat)
        try:

            await self.db.flush()

            await self.db.commit()

            await self.db.refresh(chat)
            print(f"DEBUG: Chat saved successfully. Returning chat_id: {chat.chat_id}")
            return chat.chat_id
        except Exception as e:
            print(f"ERROR: Failed to save chat. Rolling back. Error: {e}")
            await self.db.rollback()
            raise  

    async def find_similar_chunks(self, embedding: list, company_id: int, top_k: int = 5) -> list:
        """
        주어진 임베딩과 가장 유사한 청크를 데이터베이스에서 검색합니다.
        """
        try:
            embedding_str = str(embedding)
            query = text("""
            SELECT
                c.doc_id,
                c.chunk_id,
                c.metadata ->> 'content' as content,
                c.metadata ->> 'page_number' as page_number,
                d.title,
                c.embedding <=> CAST(:embedding AS vector) AS distance,
                c.weight,
                (1 - (c.embedding <=> CAST(:embedding AS vector))) * 
                CASE 
                    WHEN (1 - (c.embedding <=> CAST(:embedding AS vector))) >= 0.5 
                    THEN (1 + LEAST((c.weight - 1.0) * 0.2, 0.4))
                    ELSE 1.0
                END AS similarity_score
            FROM chunk c
            JOIN documents d ON c.doc_id = d.doc_id
            JOIN folder f ON d.folder_id = f.folder_id
            WHERE f.company_id = :company_id
            ORDER BY similarity_score DESC
            LIMIT :top_k
            """)
            
            result = await self.db.execute(
            query,
            {
                "embedding": embedding_str,
                "company_id": company_id,    
                "top_k": top_k              
            }
            )
        
            return result.fetchall() 

            
        except Exception as e:
            print(f"Error in find_similar_chunks: {e}")
            raise

        


    async def get_chunk_ids_by_chat_id(self, chat_id: int) -> list:
        """
        주어진 chat_id에 해당하는 chunk_id들을 추출합니다.
        """
        query = text("""
            SELECT chunk_ids FROM chat WHERE chat_id = :chat_id
        """)
        result = await self.db.execute(query, {"chat_id": chat_id})
        return result.fetchone()[0]

