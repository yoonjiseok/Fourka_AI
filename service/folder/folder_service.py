from typing import List, Optional

from database.repository.folder_repository import FolderRepository
from database.models import Folder
from exception.models.exception import BaseApiException


class FolderService:
    def __init__(self, folder_repository: FolderRepository):
        self.folder_repository = folder_repository

    async def create_folder(self, name: str, company_id: int) -> Folder:
        """
        새로운 폴더를 생성합니다. 동일한 회사에 동일한 이름의 폴더가 이미 존재하면 예외를 발생시킵니다.
        """
        # 동일한 회사 내에 동일한 이름의 폴더가 존재하는지 확인
        if await self.folder_repository.check_folder_exists_by_name(name, company_id):
            raise BaseApiException(
                status_code=400,
                message="폴더 생성 실패",
                reason=f"회사 ID {company_id}에 이미 '{name}'이라는 이름의 폴더가 존재합니다.",
                field="name"
            )
        
        return await self.folder_repository.create_folder(name, company_id)

    async def get_folder_by_id(self, folder_id: int) -> Folder:
        """
        ID로 폴더를 조회합니다. 폴더가 존재하지 않으면 예외를 발생시킵니다.
        """
        folder = await self.folder_repository.get_folder_by_id(folder_id)
        if not folder:
            raise BaseApiException(
                status_code=404,
                message="폴더 조회 실패",
                reason=f"ID가 {folder_id}인 폴더를 찾을 수 없습니다.",
                field="folder_id"
            )
        return folder

    async def get_folders_by_company_id(self, company_id: int) -> List[Folder]:
        """
        회사 ID에 해당하는 모든 폴더를 조회합니다.
        """
        # 회사 ID 유효성 검사 등의 로직이 필요할 수 있습니다.
        # 여기서는 단순히 repository를 호출하여 폴더를 가져옵니다.
        return await self.folder_repository.get_folders_by_company_id(company_id)

    async def update_folder_name(self, folder_id: int, new_name: str) -> Folder:
        """
        폴더 이름을 업데이트합니다. 폴더가 존재하지 않거나, 업데이트할 이름이 다른 폴더와 중복되면 예외를 발생시킵니다.
        """
        # 먼저 폴더를 조회하여 회사 ID를 가져옵니다.
        existing_folder = await self.folder_repository.get_folder_by_id(folder_id)
        if not existing_folder:
            raise BaseApiException(
                status_code=404,
                message="폴더 수정 실패",
                reason=f"ID가 {folder_id}인 폴더를 찾을 수 없습니다.",
                field="folder_id"
            )

        # 같은 회사 내에 변경하려는 이름과 동일한 이름의 다른 폴더가 있는지 확인
        if await self.folder_repository.check_folder_exists_by_name(new_name, existing_folder.company_id):
            # 단, 자기 자신의 이름이 아니라면 중복으로 간주
            if existing_folder.name != new_name:
                raise BaseApiException(
                    status_code=400,
                    message="폴더 수정 실패",
                    reason=f"회사 ID {existing_folder.company_id}에 이미 '{new_name}'이라는 이름의 다른 폴더가 존재합니다.",
                    field="name"
                )
        
        updated_folder = await self.folder_repository.update_folder_name(folder_id, new_name)
        # update_folder_name 메서드 내부에서 이미 존재 여부를 체크했지만, 한번 더 명시적으로 확인
        if not updated_folder: # 이 코드는 사실상 위에서 existing_folder 체크로 도달하지 않을 확률이 높습니다.
             raise BaseApiException(
                status_code=404,
                message="폴더 수정 실패",
                reason=f"ID가 {folder_id}인 폴더를 찾을 수 없습니다.",
                field="folder_id"
            )
        return updated_folder

    async def delete_folder(self, folder_id: int, company_id: int) -> int:
        """
        폴더를 삭제합니다. 폴더가 존재하지 않거나 소유권이 없으면 예외를 발생시킵니다.
        """
        # 삭제 전 폴더 존재 여부 확인
        existing_folder = await self.folder_repository.get_folder_by_id(folder_id)
        if not existing_folder:
            raise BaseApiException(
                status_code=404,
                message="폴더 삭제 실패",
                reason=f"ID가 {folder_id}인 폴더를 찾을 수 없습니다.",
                field="folder_id"
            )

        # 소유권 확인 로직. DB에 저장된 폴더의 company_id와 JWT에서 온 company_id가 일치하는지 확인합니다.
        if existing_folder.company_id != company_id:
            raise BaseApiException(
                status_code=403,
                message="폴더 삭제 실패",
                reason=f"해당 폴더에 대한 삭제 권한이 없습니다.",
                field="folder_id"
            )

        # 소유권이 확인되었을 때만 Repository의 삭제 함수 호출
        success = await self.folder_repository.delete_folder(folder_id, company_id)
        
        if not success:
            raise BaseApiException(
                status_code=500,
                message="폴더 삭제 실패",
                reason=f"ID가 {folder_id}인 폴더를 삭제하는 중 알 수 없는 오류가 발생했습니다."
            )
        return folder_id