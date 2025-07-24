import asyncio
from database.repository.feedback_repository import FeedbackRepository
from database.models import Feedback
from database.models import FeedbackType

class FeedbackService:
    def __init__(self, feedback_repository: FeedbackRepository):
        self.feedback_repository = feedback_repository

    async def create_feedback(self, feedback: Feedback):
        """
        피드백 타입(좋아요, 싫어요)에 따른 처리를 수행합니다.
        """
        # 피드백 타입에 따른 처리
        if feedback.feedback_type == FeedbackType.LIKE:
            # TODO: 좋아요 기능 구현 (본욱)
            raise ValueError("좋아요 기능은 아직 구현되지 않았습니다.")
            
        elif feedback.feedback_type == FeedbackType.UNLIKE:
            # 싫어요 피드백을 데이터베이스에 저장
            created_feedback = await self.feedback_repository.create_feedback(feedback)
            
        return created_feedback
    