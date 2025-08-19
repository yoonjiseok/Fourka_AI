from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Chat
from database.models import ChatType
import asyncio

class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def save_chat(self, question: str, chat_type: ChatType, chat_room_id: int, user_id: int, chunk_ids: list, faq_id : int = None) -> int:
        """채팅 메시지를 안정적으로 저장하고 생성된 ID를 반환합니다."""
        print(f"DEBUG: Saving chat for chat_room_id: {chat_room_id}")
        chat = Chat(
            question=question,
            chat_type=chat_type,
            chat_room_id=chat_room_id,
            user_id=user_id,
            chunk_ids=chunk_ids,
            faq_id = faq_id
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

    async def find_similar_chunks(self, embedding: list, company_id: int, search_query: str, top_k: int = 5) -> list:
        """
        주어진 임베딩과 검색 쿼리로 Full-text 검색과 벡터 검색을 결합한 하이브리드 검색을 수행합니다.
        RRF(Reciprocal Rank Fusion)를 사용하여 두 검색 결과의 순위를 재조합합니다.
        """
        try:
            embedding_str = str(embedding)

            # 1. Full-text 검색 쿼리
            # PostgreSQL의 to_tsvector와 plainto_tsquery를 사용합니다.
            full_text_query = text("""
            SELECT
                c.doc_id,
                c.chunk_id,
                c.metadata ->> 'content' as content,
                c.metadata ->> 'page_number' as page_number,
                d.title,
                ts_rank(to_tsvector('simple', c.metadata ->> 'content'), plainto_tsquery('simple', :search_query)) AS rank_score
            FROM chunk c
            JOIN documents d ON c.doc_id = d.doc_id
            JOIN folder f ON d.folder_id = f.folder_id
            WHERE f.company_id = :company_id AND to_tsvector('simple', c.metadata ->> 'content') @@ plainto_tsquery('simple', :search_query)
            ORDER BY rank_score DESC
            LIMIT :top_k
            """)

            # 2. 벡터 검색 쿼리
            vector_query = text("""
            SELECT
                c.doc_id,
                c.chunk_id,
                c.metadata ->> 'content' as content,
                c.metadata ->> 'page_number' as page_number,
                d.title,
                (1 - (c.embedding <=> CAST(:embedding AS vector))) AS similarity_score
            FROM chunk c
            JOIN documents d ON c.doc_id = d.doc_id
            JOIN folder f ON d.folder_id = f.folder_id
            WHERE f.company_id = :company_id
            ORDER BY similarity_score DESC
            LIMIT :top_k
            """)
            
            # 두 쿼리를 비동기적으로 실행합니다.
            full_text_result, vector_result = await asyncio.gather(
                self.db.execute(full_text_query, {"search_query": search_query, "company_id": company_id, "top_k": top_k}),
                self.db.execute(vector_query, {"embedding": embedding_str, "company_id": company_id, "top_k": top_k})
            )

            # 3. RRF를 이용한 결과 재조합
            rrf_scores = {}
            k = 60  # RRF의 가중치 파라미터입니다.

            # Full-text 검색 결과 처리
            for rank, row in enumerate(full_text_result.fetchall()):
                doc_id = (row[0], row[1])
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = {'data': row, 'score': 0}
                rrf_scores[doc_id]['score'] += 1 / (k + rank + 1)

            # 벡터 검색 결과 처리
            for rank, row in enumerate(vector_result.fetchall()):
                doc_id = (row[0], row[1])
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = {'data': row, 'score': 0}
                rrf_scores[doc_id]['score'] += 1 / (k + rank + 1)
            
            # RRF 점수 기준으로 정렬
            sorted_results = sorted(rrf_scores.values(), key=lambda x: x['score'], reverse=True)

            # 최종 결과 반환
            return [item['data'] for item in sorted_results[:top_k]]

        except Exception as e:
            print(f"Error in find_similar_chunks: {e}")
            raise


        


    async def get_chunk_ids_by_chat_id(self, chat_id: int) -> list:
        """
        주어진 chat_id에 해당하는 (doc_id, chunk_id) 튜플들을 반환합니다.
        기존 데이터는 chunk_id만 있을 수 있으므로 호환성을 위해 doc_id를 조회합니다.
        """
        query = text("""    
            SELECT chunk_ids FROM chat WHERE chat_id = :chat_id
        """)
        result = await self.db.execute(query, {"chat_id": chat_id})
        chunk_ids_data = result.fetchone()[0]
        
        if not chunk_ids_data:
            return []
        
        # chunk_ids_data가 이미 튜플 리스트인지 확인
        if chunk_ids_data and isinstance(chunk_ids_data[0], (list, tuple)):
            # 이미 (doc_id, chunk_id) 형태
            return chunk_ids_data
        
        # 기존 형태 (단순 정수 리스트)라면 doc_id를 조회하여 변환
        result_with_doc_ids = []
        for chunk_id in chunk_ids_data:
            if chunk_id is not None:
                doc_query = text("""
                    SELECT doc_id FROM chunk WHERE chunk_id = :chunk_id LIMIT 1
                """)
                doc_result = await self.db.execute(doc_query, {"chunk_id": chunk_id})
                doc_row = doc_result.fetchone()
                if doc_row:
                    result_with_doc_ids.append((doc_row[0], chunk_id))
        
        return result_with_doc_ids

    async def get_user_id_by_chat_id(self, chat_id: int) -> int | None:
        """
        주어진 chat_id에 해당하는 user_id만 조회합니다. (알림 발행용 최적화)
        """
        query = text("""
            SELECT user_id FROM chat WHERE chat_id = :chat_id
        """)
        result = await self.db.execute(query, {"chat_id": chat_id})
        row = result.fetchone()
        
        return row[0] if row else None

