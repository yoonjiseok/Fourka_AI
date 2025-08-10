from datetime import date
from database.repository.keyword_repository import KeywordRepository

class KeywordService:
    def __init__(self, keyword_repository: KeywordRepository):
        self.keyword_repository = keyword_repository

    async def get_top_keywords(
        self, company_id: int, start_date: date, end_date: date
    ) -> list[dict]:
        """Top 5 키워드 조회를 위한 비즈니스 로직을 처리합니다."""
        
        if start_date > end_date:
            raise ValueError("시작 날짜는 종료 날짜보다 클 수 없습니다.")

        top_keywords = await self.keyword_repository.get_top_keywords_by_period(
            company_id=company_id, start_date=start_date, end_date=end_date, limit=5
        )
        return top_keywords