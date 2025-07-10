from typing import Optional
from pydantic import BaseModel, Field

from model.response_models import BaseResponse

class ErrorDetail(BaseModel):
    field: Optional[str] = Field(None, description="오류가 발생한 필드 (선택 사항)")
    reason: str = Field(..., description="오류 발생 원인")

# 예외 응답을 위한 모델
# model디렉터리의 response_models를 상속하여 기본 에러 정의
class ErrorResponse(BaseResponse):
    success: bool = Field(False, description="요청 실패")
    message: str = Field("요청에 실패했습니다.", description="응답 메시지")
    code: int = Field(400, description="HTTP 상태 코드")
    error: Optional[ErrorDetail] = Field(None, description="오류 상세 정보 (선택 사항)")