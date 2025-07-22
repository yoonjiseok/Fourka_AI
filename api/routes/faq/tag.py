from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer

from api.routes.faq.faqDTO import TagCreateDTO
from dependencies.service_dependency import get_tag_service
from model.response_models import SuccessResponse
from service.faq.tag_service import TagService

tag_router = APIRouter(prefix="/api/faq-tag", tags=["FAQ Tag"])
security_scheme = HTTPBearer()


@tag_router.post("/upload", response_model=SuccessResponse)
async def upload_tag(
    # 토큰 인증 주석 처리
    #token: Annotated[HTTPAuthorizationCredentials, Security(security_scheme)],
    tag_dto: TagCreateDTO,
    tag_service: TagService = Depends(get_tag_service)
):
    """태그 등록"""
    try:
        tag = await tag_service.create_tag(
            name=tag_dto.name,
            company_id=tag_dto.company_id
        )
        
        return SuccessResponse(
            success=True,
            result={
                "tag_id": tag.tag_id,
                "name": tag.name,
                "company_id": tag.company_id,
                "created_at": tag.created_at
            },
            message="태그가 성공적으로 등록되었습니다.",
            code=200
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"태그 등록 중 오류가 발생했습니다: {str(e)}")


@tag_router.get("/{company_id}", response_model=SuccessResponse)
async def get_tags_by_company(
    # 토큰 인증 주석 처리
    #token: Annotated[HTTPAuthorizationCredentials, Security(security_scheme)],
    company_id: int,
    tag_service: TagService = Depends(get_tag_service)
):
    """회사별 태그 전체 조회"""
    try:
        tags = await tag_service.get_tags_by_company(company_id)
        
        return SuccessResponse(
            success=True,
            result=tags,
            message="태그 목록을 성공적으로 조회했습니다.",
            code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"태그 조회 중 오류가 발생했습니다: {str(e)}") 