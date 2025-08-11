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
        current_user: dict = Depends(get_current_user),
        chat_service: ChatService = Depends(get_chat_service)
):
    response = await chat_service.send_chat(
        message=request.message,
        company_id=request.company_id,
        chat_room_id=request.chat_room_id, 
        user_id=current_user.get("user_id")  
    )

    return SuccessResponse(
        result={
            "request_content": request.message,
            "response_content": response.answer,
            "meta_result": response.metadata,
        },
        message="Chatting successful",
        code=200
    )

@chat_router.post("smalltalk", response_model=SuccessResponse)
async def smalltalk(
        request: chatDTO.SmallTalkRequest,
        current_user: dict = Depends(get_current_user),
        chat_service: ChatService = Depends(get_chat_service)
):
    response = await chat_service.send_small_chat(
        message=request.message,
    )

    return SuccessResponse(
        result={
            "response": response
        },
        message="Small talk successful",
        code=200
    )