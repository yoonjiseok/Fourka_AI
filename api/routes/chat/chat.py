from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer

from api.routes.chat import chatDTO
from dependencies.auth_dependency import get_current_user
from dependencies.service_dependency import get_chat_service
from model.response_models import SuccessResponse
from service.chat.chat_service import ChatService

chat_router = APIRouter(prefix="/api/ai/chats", tags=["chat"])

security_scheme = HTTPBearer()

@chat_router.post("", response_model=SuccessResponse)
async def chatting(
        request: chatDTO.ChatRequest,
        chat_service: ChatService = Depends(get_chat_service)
):
    response = await chat_service.send_chat(
        message=request.message,
        company_id = 3,
        chat_room_id = 2, 
        # user_id=current_user.get("user_id")  
        user_id = 4
    )

    return SuccessResponse(
        result={
            "request_content": request.message,
            "response_content": response.answer,
            "meta_result": response.metadata,
            "chat_id" : response.chat_id
        },
        message="Chatting successful",
        code=200
    )
