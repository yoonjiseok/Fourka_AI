from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import FAQ # SQLAlchemy 모델
from api.routes.faq.faqDTO import FAQResponseDTO
from sqlalchemy.orm import selectinload

from exception.models.exception import FaqException
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
        try:

            self.db_session.add(db_faq)

            await self.db_session.flush()

            await self.db_session.refresh(db_faq)

            chroma_faq_service.upsert_faq(
                faq_id=db_faq.faq_id,
                question=db_faq.question,
                answer=db_faq.answer,
                company_id=db_faq.company_id,
                tag_id=db_faq.tag_id
            )
            
            # 5. 모든 작업이 성공하면 최종적으로 commit하여 트랜잭션을 완료합니다.
            await self.db_session.commit()
            
        except Exception as e:
            print(f"An error occurred. Rolling back DB transaction. Error: {e}")
            await self.db_session.rollback()
            raise FaqException(message="FAQ creation failed. Please try again later.")

        return db_faq

    async def update_faq(self, faq_id: int, question: str, answer: str, tag_id: int) -> FAQ | None:
        result = await self.db_session.execute(select(FAQ).where(FAQ.faq_id == faq_id))
        db_faq = result.scalars().first()
        
        if not db_faq:
            return None

        db_faq.question = question
        db_faq.answer = answer
        db_faq.tag_id = tag_id
        
        try:
            
            chroma_faq_service.upsert_faq(
                faq_id=db_faq.faq_id,
                question=db_faq.question,
                answer=db_faq.answer,
                company_id=db_faq.company_id,
                tag_id=db_faq.tag_id
            )

            await self.db_session.commit()

        except Exception as e:
            print(f"FAQ update failed. Rolling back DB transaction. Error: {e}")
   
            await self.db_session.rollback()
            raise FaqException(message="FAQ update failed. Please try again later.")

        await self.db_session.refresh(db_faq)
        return db_faq

    async def delete_faq(self, faq_id: int) -> bool:
        result = await self.db_session.execute(select(FAQ).where(FAQ.faq_id == faq_id))
        db_faq = result.scalars().first()

        if not db_faq:
            return False
            
        try:
            await self.db_session.delete(db_faq)
            
            chroma_faq_service.delete_faq(faq_id=faq_id)
            
            await self.db_session.commit()
            
        except Exception as e:
            await self.db_session.rollback()
            raise FaqException(message="FAQ deletion failed. Please try again later.")
            
        return True

    async def get_faqs_by_company(self, company_id: int):

        result = await self.db_session.execute(
            select(FAQ).options(selectinload(FAQ.tag)).where(FAQ.company_id == company_id)
        )
        faqs = result.scalars().all()

        faq_response = [FAQResponseDTO(
            faq_id = faq.faq_id,
            question = faq.question,
            answer = faq.answer,
            company_id = faq.company_id,
            tag_id = faq.tag_id,
            tag_name = faq.tag.name if faq.tag else None,
            created_at = faq.created_at
            )for faq in faqs
        ]
        
        return faq_response