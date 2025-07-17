from datetime import datetime

from pydantic import BaseModel, Field
from typing import Optional, Any


# 모든 응답의 기본이 되는 모델, 예외처리에서도 사용
class BaseResponse(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="응답 발생 시간")
    success: bool = Field(..., description="요청 성공 여부 (true: 성공, false: 실패)")
    message: str = Field(description="응답 메시지")
    code: int = Field(description="HTTP 상태 코드 (커스텀 코드)")

# 정상 응답을 위한 모델
# result 필드는 Any 타입으로, Optional로 없을 수도 있도록 함
class SuccessResponse(BaseResponse):
    success: bool = Field(True, description="요청 성공")
    message: str = Field("요청에 성공했습니다.", description="응답 메시지")
    code: int = Field(200, description="HTTP 상태 코드")
    result: Optional[Any] = Field(None, description="요청 처리 결과 데이터 (선택 사항)")