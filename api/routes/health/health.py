from fastapi import APIRouter
from model.response_models import SuccessResponse

health_router = APIRouter(prefix="/api/ai", tags=["Health Check"])

@health_router.get("", response_model=SuccessResponse)
async def health_check():
    """
    API 서버의 상태를 확인하는 엔드포인트입니다.
    요청 시, 서버가 정상적으로 응답 가능한 상태임을 나타내는
    성공 응답(HTTP 200)을 반환합니다.
    """
    return SuccessResponse(
        message="FourKa AI API Server is running.",
        code=200
    )