from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer

from api.routes.faq.faqDTO import FAQCreateDTO, FAQUpdateDTO, FAQDeleteDTO
from dependencies.service_dependency import get_faq_service
from dependencies.auth_dependency import get_current_user
from model.response_models import SuccessResponse
from service.faq.faq_service import FAQService

faq_router = APIRouter(prefix="/api/ai/faq", tags=["FAQ"])
security_scheme = HTTPBearer()


@faq_router.post("/upload", response_model=SuccessResponse)
async def upload_faq(
    current_user: dict = Depends(get_current_user),
    faq_service: FAQService = Depends(get_faq_service),
    faq_dto: FAQCreateDTO = Depends()
):
    """FAQ 등록"""
    try:
        faq = await faq_service.create_faq(
            question=faq_dto.question,
            answer=faq_dto.answer,
            company_id=faq_dto.company_id,
            tag_id=faq_dto.tag_id
        )
        
        return SuccessResponse(
            success=True,
            result={
                "faq_id": faq.faq_id,
                "question": faq.question,
                "answer": faq.answer,
                "tag_id": faq.tag_id,
                "created_at": faq.created_at
            },
            message="FAQ가 성공적으로 등록되었습니다.",
            code=200
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ 등록 중 오류가 발생했습니다: {str(e)}")


@faq_router.put("/update", response_model=SuccessResponse)
async def update_faq(
    current_user: dict = Depends(get_current_user),
    faq_service: FAQService = Depends(get_faq_service),
    faq_dto: FAQUpdateDTO = Depends()
):
    """FAQ 수정"""
    try:
        faq = await faq_service.update_faq(
            faq_id=faq_dto.faq_id,
            question=faq_dto.question,
            answer=faq_dto.answer,
            tag_id=faq_dto.tag_id
        )
        
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ를 찾을 수 없습니다.")
        
        return SuccessResponse(
            success=True,
            result={
                "faq_id": faq.faq_id,
                "question": faq.question,
                "answer": faq.answer,
                "tag_id": faq.tag_id
            },
            message="FAQ가 성공적으로 수정되었습니다.",
            code=200
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ 수정 중 오류가 발생했습니다: {str(e)}")


@faq_router.delete("/delete", response_model=SuccessResponse)
async def delete_faq(
    current_user: dict = Depends(get_current_user),
    faq_service: FAQService = Depends(get_faq_service),
    faq_dto: FAQDeleteDTO = Depends()
):
    """FAQ 삭제"""
    try:
        success = await faq_service.delete_faq(faq_dto.faq_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="FAQ를 찾을 수 없습니다.")
        
        return SuccessResponse(
            success=True,
            result={"faq_id": faq_dto.faq_id},
            message="FAQ가 성공적으로 삭제되었습니다.",
            code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ 삭제 중 오류가 발생했습니다: {str(e)}")


@faq_router.get("/{company_id}", response_model=SuccessResponse)
async def get_faqs_by_company(
    # 토큰 인증 주석 처리
    #token: Annotated[HTTPAuthorizationCredentials, Security(security_scheme)],
    company_id: int,
    faq_service: FAQService = Depends(get_faq_service)
):
    """회사별 FAQ 전체 조회"""
    try:
        faqs = await faq_service.get_faqs_by_company(company_id)
        
        return SuccessResponse(
            success=True,
            result=faqs,
            message="FAQ 목록을 성공적으로 조회했습니다.",
            code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ 조회 중 오류가 발생했습니다: {str(e)}") 