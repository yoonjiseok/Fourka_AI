from typing import Annotated
from fastapi import APIRouter, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from dependencies.dependency import get_chat_service
from service.chat.chat_service import ChatService
from model.response_models import SuccessResponse
from api.routes.chat import chatDTO

chat_router = APIRouter(prefix="/api/chats", tags=["chat"])

security_scheme = HTTPBearer()

@chat_router.post("", response_model=SuccessResponse)
async def chatting(
        request: chatDTO.ChatRequest,
        chat_service: ChatService = Depends(get_chat_service)
):
    response = await chat_service.send_chat(request.message)

    return SuccessResponse(
        result={
            "request_content": request.message,
            "response_content": response.answer,
            "meta_result": response.metadata,
        },
        message="Chatting successful",
        code=200
    )