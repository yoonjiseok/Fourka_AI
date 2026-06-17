from starlette.responses import JSONResponse
from fastapi import Request
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