from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from fastapi import Request, status
from exception.models.base_exception_model import ErrorResponse, ErrorDetail
from exception.models.exception import BaseApiException

def exception_handler(request: Request, exc: BaseApiException):
    """
    CustomException을 포착하여 JSON 응답으로 변환하는 핸들러.
    """
    error_detail = ErrorDetail(reason=exc.reason)

    if exc.field:
        error_detail.field = exc.field

    response_model = ErrorResponse(
        message=exc.message,
        code=exc.status_code,
        error=error_detail
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response_model.model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 유효성 검사 에러의 세부 정보 가져오기
    error_detail = exc.errors()[0]
    field_name = ".".join(map(str, error_detail["loc"]))

    # 커스텀 예외인 BaseApiException 생성
    custom_exc = BaseApiException(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="요청에 필수 필드가 누락되었거나 유효하지 않습니다.",
        reason=f"필드 '{field_name}'에 유효성 오류가 있습니다.",
        field=field_name
    )

    # 생성된 커스텀 예외를 기존 exception_handler로 전달
    return exception_handler(request, custom_exc)