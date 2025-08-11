from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    chat_room_id: int
    
class ChatResponse(BaseModel):
    answer: str
    metadata: Optional[List[dict]] = None
    chat_id : Optional[int] = None

class HILResponse(BaseModel):
    answer: str
    metadata: Optional[List[dict]]