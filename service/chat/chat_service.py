import google.generativeai as genai

from api.routes.chat import chatDTO
from config import settings
from database.repository.chat_repository import ChatRepository


class ChatService:
    def __init__(self, chat_repository: ChatRepository):
        self.chat_repository = chat_repository
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.llm_model = genai.GenerativeModel('gemini-2.5-flash')

        self.embedding_model_name = "models/embedding-001"

    async def send_chat(self, message: str) -> chatDTO.ChatResponse:

        embedding = self._text_to_embedding(message)

        print(f"DEBUG: Generated embedding dimension: {len(embedding)}")


        similar_chunks = await self.chat_repository.find_similar_chunks(embedding)

        context_parts = []
        for chunk in similar_chunks:
            try:
                content = chunk.content
                title = chunk.title
                page_number = chunk.page_number
                context_parts.append(f"문서명: {title}, 페이지: {page_number}\n내용: {content}")
            except AttributeError:
                print(f"Warning: Chunk object is missing 'content' attribute. Chunk: {chunk}")
                continue
        
        context = "\n".join(context_parts)

        # 4. 프롬프트 생성
        prompt = f"""
        당신은 사내 문서 검색 챗봇입니다. 다음 컨텍스트를 바탕으로 사용자의 질문에 답변해주세요.
        만약 컨텍스트에 답변이 없다면, "죄송합니다, 관련 정보를 찾을 수 없습니다."라고 답변해주세요.

        컨텍스트:
        {context}

        사용자 질문: {message}

        답변:
        """


        response = self.llm_model.generate_content(prompt)

        # 메타데이터
        metadata = [{"title": chunk.title, "page_number": str(chunk.page_number)} for chunk in similar_chunks]

        return chatDTO.ChatResponse(
            answer=response.text,
            metadata=metadata
        )

    def _text_to_embedding(self, text: str) -> list:
        """
        텍스트를 Google의 'embedding-001' 모델을 사용하여 벡터로 변환합니다.
        """
        result = genai.embed_content(
            model=self.embedding_model_name,
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
