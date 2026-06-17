from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Feedback


class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_feedback(self, feedback: Feedback) -> Feedback:
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback