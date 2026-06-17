from typing import List

from api.routes.faq.faqDTO import TagResponseDTO
from database.models import Tag
from database.repository.tag_repository import TagRepository


class TagService:
    def __init__(self, tag_repo: TagRepository):
        self.tag_repo = tag_repo

    async def create_tag(self, name: str, company_id: int) -> Tag:
        """태그 생성 (중복 확인 포함)"""
        # 중복 확인
        if await self.tag_repo.check_tag_exists(name, company_id):
            raise ValueError(f"'{name}' 태그가 이미 존재합니다.")
        
        tag = Tag(name=name, company_id=company_id)
        return await self.tag_repo.create_tag(tag)

    async def get_tags_by_company(self, company_id: int) -> List[TagResponseDTO]:
        """회사별 태그 조회"""
        tags = await self.tag_repo.get_tags_by_company(company_id)
        
        return [
            TagResponseDTO(
                tag_id=tag.tag_id,
                name=tag.name,
                company_id=tag.company_id,
                created_at=tag.created_at
            )
            for tag in tags
        ] 