from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List
from datetime import datetime


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
    
    # 월별 피드백 수 조회 (회사별)
    async def get_monthly_feedback_count(self, company_id: int, year: int):
        result = await self.db.execute(
            text("""
                SELECT 
                    EXTRACT(MONTH FROM created_at) as month,
                    feedback_type,
                    COUNT(*) as count
                FROM company_feedback
                WHERE company_id = :company_id 
                AND EXTRACT(YEAR FROM created_at) = :year
                GROUP BY EXTRACT(MONTH FROM created_at), feedback_type
                HAVING feedback_type = 'UNLIKE'
                ORDER BY month, feedback_type
            """),
            {"company_id": company_id, "year": year}
        )
        rows = result.fetchall()
        # 튜플을 딕셔너리로 변환
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]
    
    # 일별 피드백 수 조회 (회사별)
    async def get_daily_feedback_count(self, company_id: int, year: int, month: int):
        result = await self.db.execute(
            text("""
                SELECT 
                    EXTRACT(DAY FROM created_at) as day,
                    feedback_type,
                    COUNT(*) as count
                FROM company_feedback
                WHERE company_id = :company_id 
                AND EXTRACT(YEAR FROM created_at) = :year
                AND EXTRACT(MONTH FROM created_at) = :month
                GROUP BY EXTRACT(DAY FROM created_at), feedback_type
                HAVING feedback_type = 'UNLIKE'
                ORDER BY day, feedback_type
            """),
            {"company_id": company_id, "year": year, "month": month}
        )
        rows = result.fetchall()
        # 튜플을 딕셔너리로 변환
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]
    
    # 월별 주차별 피드백 수 조회 (회사별)
    async def get_weekly_feedback_count(self, company_id: int, year: int, month: int):
        result = await self.db.execute(
            text("""
                SELECT 
                    CEIL((EXTRACT(DAY FROM created_at) - 1) / 7.0) as week,
                    feedback_type,
                    COUNT(*) as count
                FROM company_feedback
                WHERE company_id = :company_id 
                AND EXTRACT(YEAR FROM created_at) = :year
                AND EXTRACT(MONTH FROM created_at) = :month
                GROUP BY CEIL((EXTRACT(DAY FROM created_at) - 1) / 7.0), feedback_type
                HAVING feedback_type = 'UNLIKE'
                ORDER BY week, feedback_type
            """),
            {"company_id": company_id, "year": year, "month": month}
        )
        rows = result.fetchall()
        # 튜플을 딕셔너리로 변환
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]
    
    async def get_hourly_feedback_count(self, date: str, company_id: int) -> List[dict]:
        """특정 날짜의 시간별 피드백 수를 조회합니다."""
        
        # 날짜 문자열을 date 객체로 변환
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        
        async with self.db as session:
            # 특정 회사의 시간별 피드백 수 (company_feedback 뷰 사용)
            query = text("""
                SELECT 
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as count
                FROM company_feedback
                WHERE DATE(created_at) = :date
                AND company_id = :company_id
                GROUP BY EXTRACT(HOUR FROM created_at)
                ORDER BY hour;
            """)
            result = await session.execute(query, {"date": date_obj, "company_id": company_id})
            
            rows = result.fetchall()
            
            # 0-23시간까지 모든 시간에 대해 결과 생성 (없는 시간은 0으로)
            hourly_data = {row[0]: row[1] for row in rows}
            result_list = []
            
            for hour in range(24):
                result_list.append({
                    "hour": hour,
                    "count": hourly_data.get(hour, 0)
                })
            
            return result_list

    async def get_feedback_ratio(self, company_id: int, start_date: str, end_date: str) -> dict:
        """특정 날짜 구간의 LIKE/UNLIKE 피드백 비율을 조회합니다."""
        
        # 날짜 문자열을 date 객체로 변환
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        async with self.db as session:
            query = text("""
                SELECT 
                    feedback_type,
                    COUNT(*) as count
                FROM company_feedback
                WHERE company_id = :company_id
                AND DATE(created_at) BETWEEN :start_date AND :end_date
                GROUP BY feedback_type;
            """)
            result = await session.execute(query, {
                "company_id": company_id,
                "start_date": start_date_obj,
                "end_date": end_date_obj
            })
            
            rows = result.fetchall()
            
            # 결과를 딕셔너리로 변환
            feedback_counts = {row[0]: row[1] for row in rows}
            
            # LIKE와 UNLIKE 개수 추출
            like_count = feedback_counts.get('LIKE', 0)
            unlike_count = feedback_counts.get('UNLIKE', 0)
            total_count = like_count + unlike_count
            
            # 비율 계산 (0으로 나누기 방지)
            if total_count > 0:
                like_ratio = round((like_count / total_count) * 100, 2)
                unlike_ratio = round((unlike_count / total_count) * 100, 2)
            else:
                like_ratio = 0.0
                unlike_ratio = 0.0
            
            return {
                "like_count": like_count,
                "unlike_count": unlike_count,
                "total_count": total_count,
                "like_ratio": like_ratio,
                "unlike_ratio": unlike_ratio
            }