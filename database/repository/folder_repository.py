# database/repository/folder_repository.py
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Sequence

from database.models import Folder, Document # Document 모델 임포트 필요 [cite: 170]

class FolderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_folder(self, name: str, company_id: int) -> Folder:
        """새로운 폴더를 데이터베이스에 생성합니다."""
        new_folder = Folder(name=name, company_id=company_id) # Folder 객체 생성
        self.db.add(new_folder) # 세션에 추가
        await self.db.commit() # 데이터베이스에 커밋
        await self.db.refresh(new_folder) # 최신 데이터로 객체 새로고침
        return new_folder

    async def get_folder_by_id(self, folder_id: int) -> Optional[Folder]:
        """ID로 폴더를 조회합니다."""
        result = await self.db.execute(select(Folder).where(Folder.folder_id == folder_id)) # folder_id를 기준으로 폴더 조회
        return result.scalars().first() # 첫 번째 결과 반환

    async def get_folders_by_company_id(self, company_id: int) -> List[Folder]:
        """회사 ID에 해당하는 모든 폴더를 조회합니다."""
        stmt = select(Folder).where(Folder.company_id == company_id).order_by(Folder.created_at) # company_id를 기준으로 폴더 조회, 생성 시간으로 정렬 [cite: 169]
        result = await self.db.execute(stmt)
        return list(result.scalars().all()) # 모든 결과 리스트로 반환

    async def update_folder_name(self, folder_id: int, new_name: str) -> Optional[Folder]:
        """폴더 이름을 업데이트합니다."""
        stmt = update(Folder).where(Folder.folder_id == folder_id).values(name=new_name).returning(Folder) # folder_id를 기준으로 폴더 이름을 업데이트하고 업데이트된 폴더 반환
        result = await self.db.execute(stmt)
        updated_folder = result.scalar_one_or_none() # 업데이트된 폴더 객체 가져오기
        if updated_folder:
            await self.db.commit() # 변경사항 커밋
            await self.db.refresh(updated_folder) # 최신 데이터로 새로고침
        return updated_folder

    async def delete_folder(self, folder_id: int) -> bool:
        """폴더를 삭제합니다. (연관된 문서들도 함께 삭제됩니다 - cascade 설정)"""
        # Document 모델에 cascade="all, delete-orphan" 설정이 되어 있으므로[cite: 169],
        # Folder를 삭제하면 해당 Folder에 연결된 Document들도 자동으로 삭제됩니다.
        # 또한 Document에 연결된 Chunk들도 자동으로 삭제됩니다[cite: 173].
        stmt = delete(Folder).where(Folder.folder_id == folder_id) # folder_id를 기준으로 폴더 삭제
        result = await self.db.execute(stmt)
        await self.db.commit() # 변경사항 커밋
        return result.rowcount > 0 # 삭제된 행이 1개 이상이면 True 반환

    async def check_folder_exists_by_name(self, name: str, company_id: int) -> bool:
        """같은 회사 내에 동일한 이름의 폴더가 존재하는지 확인합니다."""
        stmt = select(Folder).where(Folder.name == name, Folder.company_id == company_id) # 이름과 company_id로 폴더 존재 여부 확인 [cite: 169]
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None # 결과가 있으면 True, 없으면 False