from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from database.models import FAQ


class FAQRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_faq(self, faq: FAQ) -> FAQ:
        """FAQ 생성"""
        self.db.add(faq)
        await self.db.commit()
        await self.db.refresh(faq)
        return faq

    async def get_faq_by_id(self, faq_id: int) -> Optional[FAQ]:
        """FAQ ID로 조회"""
        stmt = select(FAQ).options(selectinload(FAQ.tag)).where(FAQ.faq_id == faq_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_faqs_by_company(self, company_id: int) -> List[FAQ]:
        """회사별 모든 FAQ 조회"""
        stmt = select(FAQ).options(selectinload(FAQ.tag)).where(FAQ.company_id == company_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_faq(self, faq_id: int, question: str, answer: str, embedding: list, tag_id: int) -> Optional[FAQ]:
        """FAQ 수정"""
        stmt = select(FAQ).where(FAQ.faq_id == faq_id)
        result = await self.db.execute(stmt)
        faq = result.scalar_one_or_none()
        
        if faq:
            faq.question = question
            faq.answer = answer
            faq.embedding = embedding
            faq.tag_id = tag_id
            await self.db.commit()
            await self.db.refresh(faq)
        
        return faq

    async def delete_faq(self, faq_id: int) -> bool:
        """FAQ 삭제"""
        stmt = select(FAQ).where(FAQ.faq_id == faq_id)
        result = await self.db.execute(stmt)
        faq = result.scalar_one_or_none()
        
        if faq:
            await self.db.delete(faq)
            await self.db.commit()
            return True
        
        return False 