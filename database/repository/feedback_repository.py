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
        """
        회사별 unlike 피드백 목록을 조회합니다.
        chat 테이블과 LEFT JOIN 하여 chat_type이 'FAQ'인 경우 faq_id를 함께 반환합니다.
        """
        result = await self.db.execute(
            text("""
                SELECT 
                    cf.*, 
                    c.faq_id
                FROM 
                    company_feedback cf
                LEFT JOIN 
                    chat c ON cf.chat_id = c.chat_id
                WHERE 
                    cf.company_id = :company_id 
                    AND cf.feedback_type = 'UNLIKE'
                ORDER BY 
                    cf.created_at DESC
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
                ORDER BY month, feedback_type
            """),
            {"company_id": company_id, "year": year}
        )
        rows = result.fetchall()

        # month별로 LIKE/UNLIKE 집계 병합
        month_map: dict[int, dict] = {}
        for row in rows:
            month = int(row[0])
            ftype = row[1]
            cnt = int(row[2])
            if month not in month_map:
                month_map[month] = {"month": month, "like_count": 0, "unlike_count": 0}
            if ftype == "LIKE":
                month_map[month]["like_count"] = cnt
            elif ftype == "UNLIKE":
                month_map[month]["unlike_count"] = cnt

        # 정렬 및 total 추가
        result_list = []
        for month in sorted(month_map.keys()):
            like_count = month_map[month]["like_count"]
            unlike_count = month_map[month]["unlike_count"]
            result_list.append({
                "month": month,
                "like_count": like_count,
                "unlike_count": unlike_count,
                "count": like_count + unlike_count
            })

        return result_list
    
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
                ORDER BY day, feedback_type
            """),
            {"company_id": company_id, "year": year, "month": month}
        )
        rows = result.fetchall()

        day_map: dict[int, dict] = {}
        for row in rows:
            day = int(row[0])
            ftype = row[1]
            cnt = int(row[2])
            if day not in day_map:
                day_map[day] = {"day": day, "like_count": 0, "unlike_count": 0}
            if ftype == "LIKE":
                day_map[day]["like_count"] = cnt
            elif ftype == "UNLIKE":
                day_map[day]["unlike_count"] = cnt

        result_list = []
        for day in sorted(day_map.keys()):
            like_count = day_map[day]["like_count"]
            unlike_count = day_map[day]["unlike_count"]
            result_list.append({
                "day": day,
                "like_count": like_count,
                "unlike_count": unlike_count,
                "count": like_count + unlike_count
            })

        return result_list
    
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
                ORDER BY week, feedback_type
            """),
            {"company_id": company_id, "year": year, "month": month}
        )
        rows = result.fetchall()

        week_map: dict[int, dict] = {}
        for row in rows:
            # 주차 계산 결과는 numeric이므로 정수화
            week = int(row[0])
            ftype = row[1]
            cnt = int(row[2])
            if week not in week_map:
                week_map[week] = {"week": week, "like_count": 0, "unlike_count": 0}
            if ftype == "LIKE":
                week_map[week]["like_count"] = cnt
            elif ftype == "UNLIKE":
                week_map[week]["unlike_count"] = cnt

        result_list = []
        for week in sorted(week_map.keys()):
            like_count = week_map[week]["like_count"]
            unlike_count = week_map[week]["unlike_count"]
            result_list.append({
                "week": week,
                "like_count": like_count,
                "unlike_count": unlike_count,
                "count": like_count + unlike_count
            })

        return result_list
    
    async def get_hourly_feedback_count(self, date: str, company_id: int) -> List[dict]:
        """특정 날짜의 시간별 피드백 수(LIKE/UNLIKE 포함)를 조회합니다."""

        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        async with self.db as session:
            query = text("""
                SELECT 
                    EXTRACT(HOUR FROM created_at) as hour,
                    feedback_type,
                    COUNT(*) as count
                FROM company_feedback
                WHERE DATE(created_at) = :date
                AND company_id = :company_id
                GROUP BY EXTRACT(HOUR FROM created_at), feedback_type
                ORDER BY hour, feedback_type;
            """)
            result = await session.execute(query, {"date": date_obj, "company_id": company_id})

            rows = result.fetchall()

            # 시간별로 LIKE/UNLIKE 카운트를 맵으로 구성
            hourly_map = {hour: {"LIKE": 0, "UNLIKE": 0} for hour in range(24)}
            for row in rows:
                hour = int(row[0])
                ftype = row[1]
                cnt = int(row[2])
                if ftype in ("LIKE", "UNLIKE"):
                    hourly_map[hour][ftype] = cnt

            # 결과 리스트 구성: 기존 total count 호환을 위해 count 필드도 제공
            result_list = []
            for hour in range(24):
                like_count = hourly_map[hour]["LIKE"]
                unlike_count = hourly_map[hour]["UNLIKE"]
                result_list.append({
                    "hour": hour,
                    "like_count": like_count,
                    "unlike_count": unlike_count,
                    "count": like_count + unlike_count
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
        
    async def delete_feedback(self, feedback_id: int) -> bool:
        """피드백 삭제 - 삭제 성공 여부를 반환합니다."""
        async with self.db as session:
            # 삭제하기 전에 존재하는지 확인
            check_query = text("SELECT feedback_id FROM feedback WHERE feedback_id = :feedback_id")
            check_result = await session.execute(check_query, {"feedback_id": feedback_id})
            existing_feedback = check_result.fetchone()
            
            if not existing_feedback:
                return False  # 존재하지 않음
            
            # 존재하면 삭제 실행
            delete_query = text("DELETE FROM feedback WHERE feedback_id = :feedback_id")
            result = await session.execute(delete_query, {"feedback_id": feedback_id})
            await session.commit()
            
            # 실제로 삭제된 행의 수를 확인 (안전장치)
            return result.rowcount > 0