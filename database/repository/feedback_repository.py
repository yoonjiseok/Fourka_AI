from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from database.models import Feedback
from database.models import FeedbackType

class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_feedback(self, feedback: Feedback) -> Feedback:
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback
    
    # 회사별 unlike 피드백 조회 (View 사용)
    async def get_company_unlike_feedback_list(self, company_id: int):
        result = await self.db.execute(
            text("""
                SELECT * FROM company_feedback 
                WHERE company_id = :company_id 
                AND feedback_type = 'UNLIKE'
                ORDER BY created_at DESC
            """),
            {"company_id": company_id}
        )
        rows = result.fetchall()
        # 튜플을 딕셔너리로 변환
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]
    
    # 회사별 모든 피드백 조회 (View 사용)
    async def get_company_feedback_list(self, company_id: int):
        result = await self.db.execute(
            text("""
                SELECT * FROM company_feedback 
                WHERE company_id = :company_id 
                ORDER BY created_at DESC
            """),
            {"company_id": company_id}
        )
        rows = result.fetchall()
        # 튜플을 딕셔너리로 변환
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]