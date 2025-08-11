from pydantic import BaseModel
from database.models import FeedbackType, FeedbackReason

class FeedbackCreateDTO(BaseModel):
    chat_id: int
    feedback_type: FeedbackType
    feedback_reason: FeedbackReason | None = None  # 선택지 (기타가 아닌 경우)
    feedback_content: str | None = None  # 사용자 입력 (기타 선택 시)
    answer: str

class TopKeywordDTO(BaseModel):
    keyword : str
    count : int