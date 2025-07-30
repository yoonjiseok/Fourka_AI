from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # HTTPBearer 임포트 

from api.routes.folder.folderDTO import (
    FolderCreateDTO,
    FolderUpdateDTO,
    FolderDeleteDTO,
    FolderGetByCompanyDTO,
    FolderResponseDTO
)
from dependencies.service_dependency import get_folder_service
from dependencies.auth_dependency import get_current_user # 사용자 인증 의존성 
from model.response_models import SuccessResponse # 공통 응답 모델 
from service.folder.folder_service import FolderService
from exception.models.exceptions import CustomException # CustomException 임포트 [cite: 81]

folder_router = APIRouter(prefix="/api/folders", tags=["Folder"]) # tags를 "Folder"로 변경하여 Swagger UI 그룹화

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
    try:
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
    except CustomException as e: # CustomException 처리 
        raise HTTPException(status_code=e.status_code, detail=jsonable_encoder(e.detail()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"폴더 생성 중 오류가 발생했습니다: {str(e)}")

@folder_router.post("/delete", response_model=SuccessResponse) # POST로 변경
async def delete_folder(
    folder_dto: FolderDeleteDTO, # 바디에서 folder_id 받음
    current_user: dict = Depends(get_current_user), # 사용자 인증 
    folder_service: FolderService = Depends(get_folder_service)
):
    """
    문서 폴더를 삭제합니다. (연관된 문서 및 청크도 함께 삭제됩니다.)
    """
    try:
        deleted_folder_id = await folder_service.delete_folder(folder_dto.folder_id)
        return SuccessResponse(
            result={"folder_id": deleted_folder_id},
            message="폴더가 성공적으로 삭제되었습니다.",
            code=200
        )
    except CustomException as e: # CustomException 처리 
        raise HTTPException(status_code=e.status_code, detail=jsonable_encoder(e.detail()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"폴더 삭제 중 오류가 발생했습니다: {str(e)}")

@folder_router.patch("/update", response_model=SuccessResponse)
async def update_folder(
    folder_dto: FolderUpdateDTO,
    current_user: dict = Depends(get_current_user), # 사용자 인증 
    folder_service: FolderService = Depends(get_folder_service)
):
    """
    문서 폴더의 이름을 수정합니다.
    """
    try:
        updated_folder = await folder_service.update_folder_name(
            folder_dto.folder_id,
            folder_dto.name
        )
        return SuccessResponse(
            result=FolderResponseDTO.model_validate(updated_folder).model_dump(),
            message="폴더 이름이 성공적으로 수정되었습니다.",
            code=200
        )
    except CustomException as e: # CustomException 처리 
        raise HTTPException(status_code=e.status_code, detail=jsonable_encoder(e.detail()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"폴더 이름 수정 중 오류가 발생했습니다: {str(e)}")

@folder_router.post("/get-by-company", response_model=SuccessResponse) # POST로 변경
async def get_all_folders_by_company(
    folder_get_dto: FolderGetByCompanyDTO, # 바디에서 company_id 받음
    current_user: dict = Depends(get_current_user), # 사용자 인증 
    folder_service: FolderService = Depends(get_folder_service)
):
    """
    특정 회사의 모든 문서 폴더를 조회합니다.
    """
    try:
        folders = await folder_service.get_folders_by_company_id(folder_get_dto.company_id)
        # 리스트 형태의 응답을 위해 각 폴더 객체를 DTO로 변환
        encoded_folders = [FolderResponseDTO.model_validate(folder).model_dump() for folder in folders]
        return SuccessResponse(
            result=encoded_folders,
            message="폴더 목록을 성공적으로 조회했습니다.",
            code=200
        )
    except CustomException as e: # CustomException 처리 
        raise HTTPException(status_code=e.status_code, detail=jsonable_encoder(e.detail()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"폴더 조회 중 오류가 발생했습니다: {str(e)}")