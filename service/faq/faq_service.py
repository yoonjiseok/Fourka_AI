import asyncio
import google.genai as genai
from typing import List, Optional

from database.models import FAQ, Tag
from database.repository.faq_repository import FAQRepository
from database.repository.tag_repository import TagRepository
from api.routes.faq.faqDTO import FAQResponseDTO
from config import settings


class FAQService:
    def __init__(self, faq_repo: FAQRepository, tag_repo: TagRepository):
        self.faq_repo = faq_repo
        self.tag_repo = tag_repo

    async def create_faq(self, question: str, answer: str, company_id: int, tag_id: int) -> FAQ:
        """FAQ 생성 (질문 임베딩 포함)"""
        tag = await self.tag_repo.get_tag_by_id(tag_id)
        if not tag or tag.company_id != company_id:
            raise ValueError("유효하지 않은 태그입니다.")
        
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, self._text_to_embedding, question)
        
        faq = FAQ(
            question=question,
            answer=answer,
            embedding=embedding,
            company_id=company_id,
            tag_id=tag_id
        )
        
        return await self.faq_repo.create_faq(faq)

    async def update_faq(self, faq_id: int, question: str, answer: str, tag_id: int) -> Optional[FAQ]:
        """FAQ 수정"""
        existing_faq = await self.faq_repo.get_faq_by_id(faq_id)
        if not existing_faq:
            raise ValueError("FAQ를 찾을 수 없습니다.")
        
        tag = await self.tag_repo.get_tag_by_id(tag_id)
        if not tag or tag.company_id != existing_faq.company_id:
            raise ValueError("유효하지 않은 태그입니다.")
        
        embedding = existing_faq.embedding
        if question != existing_faq.question:
            loop = asyncio.get_event_loop()
            # 👇 존재하지 않는 함수 호출을 제거하고, 바로 embedding 변수에 할당합니다.
            embedding = await loop.run_in_executor(None, self._text_to_embedding, question)
        
        return await self.faq_repo.update_faq(faq_id, question, answer, embedding, tag_id)

    async def delete_faq(self, faq_id: int) -> bool:
        """FAQ 삭제"""
        return await self.faq_repo.delete_faq(faq_id)

    async def get_faqs_by_company(self, company_id: int) -> List[FAQResponseDTO]:
        """회사별 FAQ 조회 (태그 정보 포함)"""
        faqs = await self.faq_repo.get_faqs_by_company(company_id)
        
        return [
            FAQResponseDTO(
                faq_id=faq.faq_id,
                question=faq.question,
                answer=faq.answer,
                company_id=faq.company_id,
                tag_id=faq.tag_id,
                tag_name=faq.tag.name,
                created_at=faq.created_at
            )
            for faq in faqs
        ]

    def _text_to_embedding(self, text: str) -> list:
        """텍스트를 768차원 임베딩으로 변환"""
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            embedding = client.models.embed_content(
                model="models/embedding-001",
                contents=text,
            )
            
            embedding_values = embedding.embeddings[0].values
            return embedding_values
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * 768