import asyncio
from database.repository.feedback_repository import FeedbackRepository
from database.repository.chunk_repository import ChunkRepository
from database.repository.chat_repository import ChatRepository
from database.models import Feedback
from database.models import FeedbackType

class FeedbackService:
    def __init__(self, feedback_repository: FeedbackRepository, chunk_repository: ChunkRepository, chat_repository: ChatRepository):
        self.feedback_repository = feedback_repository
        self.chunk_repository = chunk_repository
        self.chat_repository = chat_repository
        
    async def create_feedback(self, feedback: Feedback):
        """
        피드백 타입(좋아요, 싫어요)에 따른 처리를 수행합니다.
        """
        # 피드백 타입에 따른 처리
        if feedback.feedback_type == FeedbackType.LIKE:
            created_feedback = await self.feedback_repository.create_feedback(feedback)
            # 피드백에 있는 chat_id의 모든 chunk_id를 추출
            chunk_ids = await self.chat_repository.get_chunk_ids_by_chat_id(feedback.chat_id)
            # 해당 chat_id에 있는 chunk_id들의 가중치를 1.1배 증가
            await self.chunk_repository.update_chunk_weights(chunk_ids)
    
        elif feedback.feedback_type == FeedbackType.UNLIKE:
            # 싫어요 피드백을 데이터베이스에 저장
            created_feedback = await self.feedback_repository.create_feedback(feedback)
            
        return created_feedback
    
    async def get_company_unlike_feedback_list(self, company_id: int):
        """회사별 unlike 피드백 목록 조회 (View 사용)"""
        return await self.feedback_repository.get_company_unlike_feedback_list(company_id)
    
    async def get_company_feedback_list(self, company_id: int):
        """회사별 모든 피드백 목록 조회 (View 사용)"""
        return await self.feedback_repository.get_company_feedback_list(company_id)