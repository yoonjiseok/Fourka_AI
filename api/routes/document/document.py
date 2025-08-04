from fastapi import APIRouter, UploadFile, File, Depends, Form, BackgroundTasks, Path
from fastapi.encoders import jsonable_encoder

from api.routes.document import documentDTO
from dependencies.auth_dependency import get_current_user
from dependencies.service_dependency import get_document_service
from model import response_models
from model.response_models import SuccessResponse
from service.document.document_service import DocumentService

document_router = APIRouter(prefix="/api/ai/documents", tags=["files"])

@document_router.patch("/pdf/update")
async def update_pdf(
        documentDTO: documentDTO.UpdateDTO,
        current_user: dict = Depends(get_current_user),
        document_service: DocumentService = Depends(get_document_service),
):
    await document_service.update_file_name(
        file_id=documentDTO.doc_id,
        title=documentDTO.title
    )

    return SuccessResponse(
        result={"doc_id": documentDTO.doc_id, "title": documentDTO.title},
        message="File information updated successfully",
        code=200
    )


@document_router.post("/pdf/upload", response_model=SuccessResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
    title: str = Form(...),
    version: str = Form(...),
    folder_id: int = Form(...),
    commit_message: str = Form(...),
    file: UploadFile = File(...)
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
        save_path=save_path,
        doc_id=doc_id
    )
    
    print(f"[API_ROUTE] Background task added. Sending response to client now!")
    
    # 사용자에게 먼저 파일 정보 반환
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

@document_router.get("/version-history/{folder_id}", response_model=response_models.SuccessResponse)
async def get_version_history(
        current_user: dict = Depends(get_current_user),
        document_service: DocumentService = Depends(get_document_service),
        folder_id: int = Path(..., title="Folder ID")
):
    documents= await document_service.get_all_versions(folder_id=folder_id)
    encoded_documents = jsonable_encoder(documents)
    return response_models.SuccessResponse(result = encoded_documents)

@document_router.delete("/pdf/delete", response_model=response_models.SuccessResponse)
async def delete_pdf(
    documentDTO: documentDTO.DeleteDTO,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    delete_doc_id = await document_service.delete_pdf(doc_id=documentDTO.doc_id)
    return response_models.SuccessResponse(result= {"doc_id": delete_doc_id}, message="File deleted successfully", code=200)

@document_router.post("/change/main", response_model=response_models.SuccessResponse)
async def change_main_document(
    maindocumentDTO: documentDTO.ChangeMainDocumentDTO,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    updated_doc_id = await document_service.change_main_document(
        doc_id=maindocumentDTO.doc_id,
        folder_id=maindocumentDTO.folder_id
    )
    return response_models.SuccessResponse(
        result={"doc_id": updated_doc_id},
        message="Main document changed successfully",
        code=200
)
