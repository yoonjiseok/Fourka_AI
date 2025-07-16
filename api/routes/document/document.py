from fastapi import APIRouter, Security, UploadFile, File, Depends, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated

from dependencies.dependency import get_document_service
from api.routes.document import documentDTO
from service.document.document_service import DocumentService
from model.response_models import SuccessResponse

document_router = APIRouter(prefix="/api/documents", tags=["files"])


security_scheme = HTTPBearer()

@document_router.patch("/pdf/update")
async def update_pdf(
        token: Annotated[HTTPAuthorizationCredentials, Security(security_scheme)],
        fileinfo: documentDTO.UpdateDTO,
        document_service: DocumentService = Depends(get_document_service)
):
    await document_service.update_file_name(
        file_id=fileinfo.doc_id,
        title=fileinfo.title
    )

    return SuccessResponse(
        result={"doc_id": doc_id, "title": doc_title},
        message="File information updated successfully",
        code=200
    )


@document_router.post("/pdf/upload", response_model=SuccessResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    version: str = Form(...),
    folder_id: int = Form(...),
    commit_message: str = Form(...),
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service)
):
    print(f"[API_ROUTE] Starting PDF upload endpoint for file: {file.filename}")
    
    doc_id, doc_title, doc_version, doc_created_at, save_path = await document_service.upload_pdf(
        file=file,
        title=title,
        version=version,
        folder_id=folder_id,
        commit_message=commit_message
    )
    
    print(f"[API_ROUTE] Service upload_pdf completed. Adding background task...")
    
    # 백그라운드에서 청크 분석 및 저장
    background_tasks.add_task(
        document_service.process_pdf_chunks,
        save_path, title, version, folder_id, commit_message, doc_id
    )
    
    print(f"[API_ROUTE] Background task added. Sending response to client now!")
    
    return SuccessResponse(
        result={
            "doc_id": doc_id,
            "title": doc_title,
            "version": doc_version,
            "created_at": doc_created_at
        },
        message="File uploaded successfully",
        code=200
    )