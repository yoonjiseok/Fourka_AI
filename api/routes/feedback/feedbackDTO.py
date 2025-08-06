from pydantic import BaseModel
from database.models import FeedbackType

class FeedbackCreateDTO(BaseModel):
    chat_id: int
    feedback_type: FeedbackType
    feedback_content: str
    answer: str