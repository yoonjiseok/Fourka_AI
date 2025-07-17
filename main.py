from fastapi import FastAPI
from api.routes.chat.chat import chat_router
from api.routes.document.document import document_router
from database import models
from utils.db import async_engine
import asyncio

app = FastAPI(
    title="CHATBOT",
    description="Rag AI Chatbot ",
)

@app.on_event("startup")
async def startup_event():
    async with async_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

app.include_router(chat_router)
app.include_router(document_router)
