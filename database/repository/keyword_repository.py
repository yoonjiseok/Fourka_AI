# database/repository/keyword_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from database.models import KeywordLog

class KeywordRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_keywords(self, keywords: List[str], company_id: int, chat_id: int):
        """추출된 키워드 목록을 데이터베이스에 저장합니다."""
        if not keywords:
            return

        new_logs = [
            KeywordLog(keyword=kw, company_id=company_id, chat_id=chat_id)
            for kw in keywords
        ]
        self.db.add_all(new_logs)
        await self.db.commit()
        print(f"DEBUG: 키워드 {keywords}를 DB에 저장했습니다.")
