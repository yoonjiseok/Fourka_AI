from typing import Optional

# 1. 최상위 부모 예외 클래스 (변경 없음)
class BaseApiException(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        reason: str,
        field: Optional[str] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.field = field
        self.reason = reason
        super().__init__(message)

class ChatException(BaseApiException):
    def __init__(
            self,
            status_code: int = 500,
            message: str = "채팅 관련 요청에 실패했습니다.",
            reason: str = "채팅 처리 중 오류가 발생했습니다.",
            field: Optional[str] = "chat",
                 ):
        super().__init__(status_code, message, reason, field)



class DocumentException(BaseApiException):
    def __init__(
        self,
        status_code: int = 500,
        message: str = "문서 관련 요청에 실패했습니다.",
        reason: str = "문서 처리 중 오류가 발생했습니다.",
        field: Optional[str] = "document",
    ):
        super().__init__(status_code, message, reason, field)


class FaqException(BaseApiException):
    def __init__(
        self,
        status_code: int = 500,
        message: str = "FAQ 관련 요청에 실패했습니다.",
        reason: str = "FAQ 처리 중 오류가 발생했습니다.",
        field: Optional[str] = "faq",
    ):
        super().__init__(status_code, message, reason, field)

class FeedbackException(BaseApiException):
    def __init__(
        self,
        status_code: int = 500,
        message: str = "피드백 관련 요청에 실패했습니다.",
        reason: str = "피드백 처리 중 오류가 발생했습니다.",
        field: Optional[str] = "feedback",
    ):
        super().__init__(status_code, message, reason, field)

class AIException(BaseApiException):
    def __init__(
        self,
        status_code: int = 500,
        message: str = "AI 관련 요청에 실패했습니다.",
        reason: str = "AI 처리 중 오류가 발생했습니다.",
        field: Optional[str] = "ai",
    ):
        super().__init__(status_code, message, reason, field)

class FolderException(BaseApiException):
    def __init__(
        self,
        status_code: int = 500,
        message: str = "폴더 관련 요청에 실패했습니다.",
        reason: str = "폴더 처리 중 오류가 발생했습니다.",
        field: Optional[str] = "folder",
    ):
        super().__init__(status_code, message, reason, field)
