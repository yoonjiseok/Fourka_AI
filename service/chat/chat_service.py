from database.repository.chat_repository import ChatRepository
from google import genai
from config import settings
from api.routes.chat import chatDTO

class ChatService:
    def __init__(self, chat_repository: ChatRepository):
        self.chat_repository = chat_repository
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    async def send_chat(self, message: str) -> chatDTO.ChatResponse:
        # 1. 사용자 질문을 임베딩으로 변환
        embedding = self._text_to_embedding(message)

        # 2. 유사한 청크 검색
        similar_chunks = await self.chat_repository.find_similar_chunks(embedding)

        # 3. LLM에 전달할 컨텍스트 생성
        context = "\n".join([f"문서명: {chunk.title}, 페이지: {chunk.page_number}\n내용: {chunk.content}" for chunk in similar_chunks])

        # 4. 프롬프트 생성
        prompt = f"""
        당신은 사내 문서 검색 챗봇입니다. 다음 컨텍스트를 바탕으로 사용자의 질문에 답변해주세요.
        만약 컨텍스트에 답변이 없다면, "죄송합니다, 관련 정보를 찾을 수 없습니다."라고 답변해주세요.

        컨텍스트:
        {context}

        사용자 질문: {message}

        답변:
        """

        # 5. LLM API 호출
        response = self.model.generate_content(prompt)

        # 6. 메타데이터 생성
        metadata = [{"title": chunk.title, "page_number": chunk.page_number} for chunk in similar_chunks]

        return chatDTO.ChatResponse(
            answer=response.text,
            metadata=metadata
        )

    def _text_to_embedding(self, text: str) -> list:
        """
        텍스트를 임베딩 벡터로 변환합니다.
        """
        embedding_result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return embedding_result['embedding']