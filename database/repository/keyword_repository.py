# database/repository/keyword_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from database.models import KeywordLog
from sqlalchemy import text
from datetime import date
from datetime import timedelta

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

    async def get_top_keywords_by_period(
        self, company_id: int, start_date: date, end_date: date, limit: int = 5
    ) -> list[dict]:
        """
        주어진 기간과 회사 ID에 대해 가장 많이 등장한 키워드 Top N을 조회합니다.
        """
  
        
        end_date_exclusive = end_date + timedelta(days=1)

        query = text(
            """
            SELECT
                keyword,
                COUNT(*) AS count
            FROM
                keyword_log
            WHERE
                company_id = :company_id
                AND created_at >= :start_date
                AND created_at < :end_date_exclusive
            GROUP BY
                keyword
            ORDER BY
                count DESC
            LIMIT :limit;
            """
        )

        result = await self.db.execute(
            query,
            {
                "company_id": company_id,
                "start_date": start_date,
                "end_date_exclusive": end_date_exclusive,
                "limit": limit,
            },
        )
        
        return [dict(row) for row in result.mappings()]

