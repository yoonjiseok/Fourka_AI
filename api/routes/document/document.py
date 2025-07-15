from fastapi import APIRouter, Security, UploadFile, File, Depends, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated

from dependencies.dependency import get_document_service
from api.routes.document import documentDTO
from model.response_models import SuccessResponse
from service.document.document_service import DocumentService

document_router = APIRouter(prefix="/api/documents", tags=["files"])


security_scheme = HTTPBearer()

@document_router.patch("/pdf/update")
async def update_pdf(
        token: Annotated[HTTPAuthorizationCredentials, Security(security_scheme)],
        fileinfo: documentDTO.UpdateDTO,
        document_service: DocumentService = Depends(get_document_service)
):
    doc_id, doc_title = await document_service.update_file_name(
        file_id=fileinfo.doc_id,
        title=fileinfo.title
    )

    return SuccessResponse(
        result={"doc_id": doc_id, "title": doc_title},
        message="File information updated successfully",
        code=200
    )


@document_router.post("/pdf/upload")
async def upload_pdf(
    title: str = Form(...),
    version: str = Form(...),
    folder_id: int = Form(...),
    commit_message: str = Form(...),
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service)
):
    # Form 데이터를 DTO로 변환
    fileinfo = documentDTO.UploadDTO(
        title=title,
        version=version,
        folder_id=folder_id,
        commit_message=commit_message
    )
    
    doc_id, doc_title, doc_version, doc_created_at = await document_service.upload_pdf(
        file=file,
        title=fileinfo.title,
        version=fileinfo.version,
        folder_id=fileinfo.folder_id,
        commit_message=fileinfo.commit_message
    )

    return SuccessResponse(
        result={"doc_id": doc_id, "title": doc_title, "version": doc_version, "created_at": doc_created_at},
        message="File uploaded successfully",
        code=200
    )