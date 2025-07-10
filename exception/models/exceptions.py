from typing import Optional


class CustomException(Exception):
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


# 예시
class UserNotFoundError(CustomException):
    def __init__(self, user_id: int):
        # 부모 클래스의 __init__에 필요한 모든 값을 여기서 정의하여 전달합니다.
        super().__init__(
            status_code=404,
            message="사용자를 찾을 수 없습니다.",
            reason=f"ID가 {user_id}인 사용자는 존재하지 않습니다."
        )
# 후에 이거 던지면 핸들러에서 잡음