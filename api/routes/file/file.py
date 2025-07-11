from typing import Annotated

from fastapi import APIRouter, Security, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import service.file.file_service as file_service
from api.routes.chat.chat import chat_router
from api.routes.file import fileDTO

file_router = APIRouter(prefix="/api/files", tags=["files"])


security_scheme = HTTPBearer()


@chat_router.post("/pdf/upload")
async def upload_pdf(
        token: Annotated[HTTPAuthorizationCredentials, Security(security_scheme)],
        file: Annotated[UploadFile, File(..., description="업로드할 PDF 파일")]
):
    result = file_service.read_file(file)


@chat_router.post("/pdf/update")
async def update_pdf(
        token: Annotated[HTTPAuthorizationCredentials, Security(security_scheme)],
        fileinfo: fileDTO.UpdateDTO
):
    result = file_service.read_file(fileinfo)
