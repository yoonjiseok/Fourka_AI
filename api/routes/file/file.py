from fastapi import APIRouter, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated

from api.routes.file import fileDTO
from dependencies.dependency import get_file_service
from service.file.file_service import FileService

file_router = APIRouter(prefix="/api/files", tags=["files"])


security_scheme = HTTPBearer()

@file_router.patch("/pdf/update")
async def update_pdf(
        token: Annotated[HTTPAuthorizationCredentials, Security(security_scheme)],
        fileinfo: fileDTO.UpdateDTO,
        file_service: FileService = Depends(get_file_service)
):
    await file_service.update_file_name(
        file_id=fileinfo.doc_id,
        title=fileinfo.title
    )

    return {"message": "File information updated successfully"}

@file_router.get("/version-history")
async def get_version_history(
        token: Annotated[HTTPAuthorizationCredentials, Security(security_scheme)],
        folder_info: fileDTO.folderDTO,
        file_service: FileService = Depends(get_file_service)
):
    documents= await file_service.get_all_versions(folder_id=folder_info.folder_id)
    return documents