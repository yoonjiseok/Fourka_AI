from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import FAQ # SQLAlchemy 모델
# ChromaDB 서비스 임포트
from service.chroma_service import chroma_faq_service

class FAQService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session


    async def create_faq(self, question: str, answer: str, company_id: int, tag_id: int) -> FAQ:

        db_faq = FAQ(
            question=question,
            answer=answer,
            company_id=company_id,
            tag_id=tag_id
        )
        self.db_session.add(db_faq)
        await self.db_session.commit()
        await self.db_session.refresh(db_faq)

        chroma_faq_service.upsert_faq(
            faq_id=db_faq.faq_id,
            question=db_faq.question,
            answer=db_faq.answer,
            company_id=db_faq.company_id,
            tag_id=db_faq.tag_id
        )
        
        return db_faq

    async def update_faq(self, faq_id: int, question: str, answer: str, tag_id: int) -> FAQ | None:

        result = await self.db_session.execute(select(FAQ).where(FAQ.faq_id == faq_id))
        db_faq = result.scalars().first()
        
        if db_faq:
            db_faq.question = question
            db_faq.answer = answer
            db_faq.tag_id = tag_id
            await self.db_session.commit()
            await self.db_session.refresh(db_faq)

            chroma_faq_service.upsert_faq(
                faq_id=db_faq.faq_id,
                question=db_faq.question,
                answer=db_faq.answer,
                company_id=db_faq.company_id,
                tag_id=db_faq.tag_id
            )
            return db_faq
        return None

    async def delete_faq(self, faq_id: int) -> bool:

        result = await self.db_session.execute(select(FAQ).where(FAQ.faq_id == faq_id))
        db_faq = result.scalars().first()

        if db_faq:
            await self.db_session.delete(db_faq)
            await self.db_session.commit()
            
            chroma_faq_service.delete_faq(faq_id=faq_id)
            
            return True
        return False

    async def get_faqs_by_company(self, company_id: int):

        result = await self.db_session.execute(select(FAQ).where(FAQ.company_id == company_id))
        faqs = result.scalars().all()
        return faqs