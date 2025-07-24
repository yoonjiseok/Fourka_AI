from fastapi import FastAPI
from api.routes.chat.chat import chat_router
from api.routes.document.document import document_router
from api.routes.faq.faq import faq_router
from api.routes.faq.tag import tag_router
from api.routes.feedback.feedback import feedback_router
from database import models
from utils.db import async_engine
import asyncio

app = FastAPI(
    title="CHATBOT",
    description="Rag AI Chatbot ",
)

# 테이블 생성은 이제 Alembic으로 관리됩니다
# 마이그레이션 적용: alembic upgrade head

app.include_router(chat_router)
app.include_router(document_router)
app.include_router(faq_router)
app.include_router(tag_router)
app.include_router(feedback_router)
