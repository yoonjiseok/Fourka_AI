from urllib.request import Request

from starlette.responses import JSONResponse

from exception.models.base_exception_model import ErrorResponse, ErrorDetail
from exception.models.exceptions import CustomException
from main import app


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    """
    CustomException을 ErrorResponse 형식으로 변환하는 핸들러
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.message,
            error=ErrorDetail(
                field=exc.field,
                reason=exc.reason,
            ),
        ).model_dump(exclude_none=True),
    )
