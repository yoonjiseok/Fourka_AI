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
    
    async def delete_tag(self, tag_id: int) -> int:
        """
        태그를 삭제합니다. 만약 해당 태그를 사용하는 FAQ가 있다면 예외를 발생시킵니다.
        """
        # 1. 태그를 사용하는 FAQ가 있는지 확인해 데이터 무결성을 보장
        if await self.tag_repo.is_tag_in_use(tag_id):
            raise ValueError("해당 태그를 사용하고 있는 FAQ가 있어 삭제할 수 없습니다.")

        # 2. Repository를 통해 태그를 삭제
        success = await self.tag_repo.delete_tag_by_id(tag_id)

        # 3. 만약 삭제에 실패했다면 (존재하지 않는 태그 ID), 예외를 발생시킵니다.
        if not success:
            raise ValueError("존재하지 않는 태그입니다.")

        return tag_id
    