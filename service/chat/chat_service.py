from .chat_graph import ChatGraph # 위에서 만든 클래스 import
from database.repository.chat_repository import ChatRepository
from database.repository.company_repository import CompanyRepository
from api.routes.chat import chatDTO

class ChatService:
    def __init__(self, chat_repository: ChatRepository, company_repository: CompanyRepository):
        
        chat_graph_manager = ChatGraph(
            chat_repository=chat_repository,
            company_repository=company_repository
        )
        self.app = chat_graph_manager.create_graph()

    async def send_chat(self, message: str, company_id: int, chat_room_id: int, user_id: int):
        
        initial_state = {
            "user_question": message,
            "company_id": company_id,
            "chat_room_id": chat_room_id,
            "user_id": user_id
        }
        
        final_state = await self.app.ainvoke(initial_state)

        return chatDTO.ChatResponse(
            answer=final_state['final_answer'],
            metadata=final_state['final_metadata']
        )