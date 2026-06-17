from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    company_id: int
    chat_room_id: int
    
class ChatResponse(BaseModel):
    answer: str
    metadata: Optional[List[dict]] = None

class HILResponse(BaseModel):
    answer: str
    metadata: Optional[List[dict]]