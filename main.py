from fastapi import FastAPI
from api.routes.chat.chat import chat_router
from api.routes.file.file import file_router

app = FastAPI(
    title="CHATBOT",
    description="Rag AI Chatbot ",
)


app.include_router(chat_router)
app.include_router(file_router)