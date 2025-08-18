from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.routes.chat.chat import chat_router
from api.routes.document.document import document_router
from api.routes.faq.faq import faq_router
from api.routes.faq.tag import tag_router
from api.routes.feedback.feedback import feedback_router
from api.routes.folder.folder import folder_router
from api.routes.health.health import health_router
from exception.exception_handler import exception_handler, validation_exception_handler
from exception.models.exception import BaseApiException
from utils.db import async_engine
from database.models import Base

app = FastAPI(
    title="CHATBOT",
    description="Rag AI Chatbot ",
)

# 테이블 생성은 이제 Alembic으로 관리됩니다
# 마이그레이션 적용: alembic upgrade head

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(document_router)
app.include_router(faq_router)
app.include_router(tag_router)
app.include_router(feedback_router)
app.include_router(folder_router)

# 채팅 예외 핸들러
app.exception_handler(BaseApiException)(exception_handler)
app.exception_handler(RequestValidationError)(validation_exception_handler)

@app.on_event("startup")
async def init_db() -> None:
    """서버 기동 시, 존재하지 않는 테이블을 models 기준으로 생성합니다."""
    async with async_engine.begin() as conn:
    
        await conn.run_sync(Base.metadata.create_all)