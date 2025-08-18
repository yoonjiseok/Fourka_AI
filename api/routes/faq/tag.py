from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer

from api.routes.faq.faqDTO import TagCreateDTO
from dependencies.service_dependency import get_tag_service
from dependencies.auth_dependency import get_current_user
from model.response_models import SuccessResponse
from service.faq.tag_service import TagService

tag_router = APIRouter(prefix="/api/ai/faq-tag", tags=["FAQ Tag"])
security_scheme = HTTPBearer()


@tag_router.post("/upload", response_model=SuccessResponse)
async def upload_tag(
    tag_dto: TagCreateDTO,
    current_user: dict = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service)
):
    """태그 등록"""
    try:
        if len(tag_dto.title) == 0:
            raise RequestValidationError(errors=[{"loc": ["body", "missing_field"], "msg": "필수 필드가 누락되었습니다."}])
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


@tag_router.get("", response_model=SuccessResponse)
async def get_tags_by_company(
    current_user: dict = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
):
    """회사별 태그 전체 조회"""
    try:
        company_id = current_user.get("company_id")
        
        # 토큰에 company_id가 없는 경우 예외 처리
        if not company_id:
            raise HTTPException(
                status_code=403,
                detail="요청 권한이 없습니다 (토큰에 회사 정보가 없습니다)."
            )

        tags = await tag_service.get_tags_by_company(company_id)
        
        return SuccessResponse(
            success=True,
            result=tags,
            message="태그 목록을 성공적으로 조회했습니다.",
            code=200
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        # 그 외의 예외는 500 오류로 처리합니다.
        raise HTTPException(status_code=500, detail=f"태그 조회 중 오류가 발생했습니다: {str(e)}")

@tag_router.delete("/delete/{tag_id}", response_model=SuccessResponse)
async def delete_tag(
    tag_id: int = Path(..., title="Tag ID", description="삭제할 태그의 ID"),
    current_user: dict = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
):
    """
    지정된 ID의 태그를 삭제합니다.
    - tag_id: 삭제할 태그의 고유 ID
    - 제약조건: 해당 태그를 사용 중인 FAQ가 하나라도 있으면 삭제할 수 없습니다.
    """
    try:
        deleted_tag_id = await tag_service.delete_tag(tag_id)
        return SuccessResponse(
            success=True,
            result={"tag_id": deleted_tag_id},
            message="태그가 성공적으로 삭제되었습니다.",
            code=200
        )
    except ValueError as e:
        # 서비스 계층에서 발생시킨 예외 (400 Bad Request)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 그 외 예상치 못한 서버 오류 (500 Internal Server Error)
        raise HTTPException(status_code=500, detail=f"태그 삭제 중 오류가 발생했습니다: {str(e)}")