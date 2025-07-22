from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from database.models import Tag


class TagRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tag(self, tag: Tag) -> Tag:
        """태그 생성"""
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        """태그 ID로 조회"""
        stmt = select(Tag).where(Tag.tag_id == tag_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tags_by_company(self, company_id: int) -> List[Tag]:
        """회사별 모든 태그 조회"""
        stmt = select(Tag).where(Tag.company_id == company_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def check_tag_exists(self, name: str, company_id: int) -> bool:
        """같은 회사 내에서 태그명 중복 확인"""
        stmt = select(Tag).where(Tag.name == name, Tag.company_id == company_id)
        result = await self.db.execute(stmt)
        tag = result.scalar_one_or_none()
        return tag is not None 