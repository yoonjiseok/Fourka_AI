from fastapi import APIRouter, Security, UploadFile, File, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated

from api.dependencies.dependency import get_file_service
from api.routes.file import fileDTO
from service.file import file_service
from service.file.file_service import FileService

file_router = APIRouter(prefix="/api/files", tags=["files"])


security_scheme = HTTPBearer()


@file_router.post("/pdf/upload")
async def upload_pdf(
        token: Annotated[HTTPAuthorizationCredentials, Security(security_scheme)],
        file: Annotated[UploadFile, File(..., description="업로드할 PDF 파일")]
):
    result = file_service.read_file(file)


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