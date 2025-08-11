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
    faq_dto: FAQCreateDTO,
    current_user: dict = Depends(get_current_user),
    faq_service: FAQService = Depends(get_faq_service),
):
    """FAQ 등록"""
    try:
        faq = await faq_service.create_faq(
            question=faq_dto.question,
            answer=faq_dto.answer,
            company_id=current_user.get("company_id"),
            tag_id=faq_dto.tag_id
        )
        
        return SuccessResponse(
            success=True,
            result={
                "faq_id": faq.faq_id,
                "company_id": faq.company_id,
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
    faq_dto: FAQUpdateDTO,
    current_user: dict = Depends(get_current_user),
    faq_service: FAQService = Depends(get_faq_service),
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
    faq_dto: FAQDeleteDTO,
    current_user: dict = Depends(get_current_user),
    faq_service: FAQService = Depends(get_faq_service),
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


@faq_router.get("", response_model=SuccessResponse)
async def get_faqs_by_company(
    current_user: dict = Depends(get_current_user),
    faq_service: FAQService = Depends(get_faq_service)
):
    """회사별 FAQ 전체 조회 (토큰 인증 기반)"""
    try:
        # 토큰에 담긴 사용자 정보에서 company_id를 가져옵니다.
        company_id = current_user["company_id"]
        
        faqs = await faq_service.get_faqs_by_company(company_id)
        
        return SuccessResponse(
            success=True,
            result=faqs,
            message="FAQ 목록을 성공적으로 조회했습니다.",
            code=200
        )
    except KeyError:
        # 토큰에 company_id가 없는 경우 예외 처리
        raise HTTPException(status_code=401, detail="JWT 토큰에 company_id가 포함되어 있지 않습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ 조회 중 오류가 발생했습니다: {str(e)}")