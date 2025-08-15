from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from database.models import Company # 데이터베이스 모델 import

class CompanyRepository:
    def __init__(self, db: AsyncSession):
        """
        데이터베이스 세션을 주입받아 초기화합니다.
        """
        self.db = db

    async def find_by_company_id(self, company_id: int) -> Optional[Company]:
        """
        회사 ID로 회사 정보를 조회합니다.
        """
        stmt = select(Company).where(Company.company_id == company_id)
        
        result = await self.db.execute(stmt)
        
        return result.scalar_one_or_none()
    
    async def think_level_find_by_company_id(self, company_id: int) -> Optional[Company]:
        """
        회사 ID로 회사 think_level 를 조회합니다.
        """
        stmt = select(Company.think_level).where(Company.company_id == company_id)
        
        result = await self.db.execute(stmt)
        
        return result.scalar_one_or_none()
    
    async def speech_level_find_by_company_id(self, company_id: int) -> Optional[Company]:
        """
        회사 ID로 회사 speech_level 를 조회합니다.
        """
        stmt = select(Company.speech_level).where(Company.company_id == company_id)
        
        result = await self.db.execute(stmt)
        
        return result.scalar_one_or_none()