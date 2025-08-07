from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer  # HTTPBearer 임포트

from api.routes.folder.folderDTO import (
    FolderCreateDTO,
    FolderUpdateDTO,
    FolderDeleteDTO,
    FolderResponseDTO
)
from dependencies.auth_dependency import get_current_user  # 사용자 인증 의존성
from dependencies.service_dependency import get_folder_service
from exception.models.exception import FolderException
from model.response_models import SuccessResponse  # 공통 응답 모델
from service.folder.folder_service import FolderService

folder_router = APIRouter(prefix="/api/ai/folders", tags=["Folder"]) # tags를 "Folder"로 변경하여 Swagger UI 그룹화

security_scheme = HTTPBearer() # 인증 스키마 

@folder_router.post("/upload", response_model=SuccessResponse)
async def upload_folder(
    folder_dto: FolderCreateDTO,
    current_user: dict = Depends(get_current_user), # 사용자 인증 
    folder_service: FolderService = Depends(get_folder_service)
):
    """
    새로운 문서 폴더를 생성합니다.
    """

    new_folder = await folder_service.create_folder(
        name=folder_dto.name,
        company_id=folder_dto.company_id
    )
    # FolderResponseDTO를 사용하여 응답 결과 형식을 맞춥니다.
    return SuccessResponse(
        result=FolderResponseDTO.model_validate(new_folder).model_dump(), # Pydantic v2 .model_dump() 사용
        message="폴더가 성공적으로 생성되었습니다.",
        code=200
    )


@folder_router.delete("/delete", response_model=SuccessResponse)
async def delete_folder(
    folder_dto: FolderDeleteDTO, # 바디에서 folder_id 받음
    current_user: dict = Depends(get_current_user), # 사용자 인증 
    folder_service: FolderService = Depends(get_folder_service)
):
    """
    문서 폴더를 삭제합니다. (연관된 문서 및 청크도 함께 삭제됩니다.)
    """
    try:
        # 1. JWT 토큰에서 company_id를 가져옵니다.
        company_id = current_user["company_id"]

        # 2. 서비스 함수에 folder_id와 company_id를 함께 전달합니다.
        deleted_folder_id = await folder_service.delete_folder(folder_dto.folder_id, company_id)
        
        return SuccessResponse(
            result={"folder_id": deleted_folder_id},
            message="폴더가 성공적으로 삭제되었습니다.",
            code=200
        )
    except KeyError: # JWT에 company_id가 없을 경우를 대비한 예외 처리
        raise FolderException(
            status_code=401, message="인증오류",
            reason="유효한 토큰이 아니거나 토큰에 company_id가 없습니다.", field="token"
            )
    
@folder_router.patch("/update", response_model=SuccessResponse)
async def update_folder(
    folder_dto: FolderUpdateDTO,
    current_user: dict = Depends(get_current_user), # 사용자 인증 
    folder_service: FolderService = Depends(get_folder_service)
):
    """
    문서 폴더의 이름을 수정합니다.
    """
    updated_folder = await folder_service.update_folder_name(
        folder_dto.folder_id,
        folder_dto.name
    )
    return SuccessResponse(
        result=FolderResponseDTO.model_validate(updated_folder).model_dump(),
        message="폴더 이름이 성공적으로 수정되었습니다.",
        code=200
    )

@folder_router.get("", response_model=SuccessResponse)
async def get_all_folders_by_company(
    current_user: dict = Depends(get_current_user), # 사용자 인증 
    folder_service: FolderService = Depends(get_folder_service)
):
    """
    특정 회사의 모든 문서 폴더를 조회합니다.
    """
    try:
        # current_user 딕셔너리에서 company_id를 직접 가져옵니다.
        company_id = current_user["company_id"]
        folders = await folder_service.get_folders_by_company_id(company_id)
        
        encoded_folders = [FolderResponseDTO.model_validate(folder).model_dump() for folder in folders]
        return SuccessResponse(
            result=encoded_folders,
            message="폴더 목록을 성공적으로 조회했습니다.",
            code=200
        )
    except KeyError: # JWT에 company_id가 없을 경우를 대비한 예외 처리
        raise FolderException(
            status_code=401, message="인증오류",
            reason="유효한 토큰이 아니거나 토큰에 company_id가 없습니다.", field="token"
            )
