import google.generativeai as genai
from typing import List

from api.routes.chat import chatDTO
from config import settings
from database.repository.chat_repository import ChatRepository
from service.chat import HIL_service


class ChatService:
    def __init__(self, chat_repository: ChatRepository):
        self.chat_repository = chat_repository
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.llm_model = genai.GenerativeModel('gemini-2.5-flash')

        self.embedding_model_name = "models/embedding-001"

    async def send_chat(self, message: str) -> chatDTO:

        embedding = self._text_to_embedding(message)

        print(f"DEBUG: Generated embedding dimension: {len(embedding)}")

        similar_chunks = await self.chat_repository.find_similar_chunks(embedding)

        context_list = []
        for chunk in similar_chunks:
            try:
                chunk_dict = {
                    "title": chunk.title,
                    "page_number": chunk.page_number,
                    "content": chunk.content,
                }
                context_list.append(chunk_dict)
            except AttributeError:
                print(f"Warning: Chunk object is missing 'content' attribute. Chunk: {chunk}")
                continue
        print(f"DEBUG: created context list: {context_list}")




        ###################################################
        # TODO (하림)
        """
        만약 검색된 모든 청크의 유사도가 임계값 이하라면, HIL 서비스를 실행합니다.
        """
        # 추후 MSA로 구성된 백엔드의 Company 데이터베이스에서 think_level값을 받아와서 threshold 값으로 설정합니다.
        HIL_flag = HIL_service.similar_chunks(similar_chunks, threshold=0.7)
        if HIL_flag:
            # 모든 청크의 유사도가 0.7 미만일때 HIL 서비스를 실행합니다.
            print("DEBUG: HIL 서비스 실행")
            return HIL_service.HIL(context_list)

        ####################################################



        # 4. 프롬프트 생성
        prompt = f"""
        당신은 사내 문서 검색 챗봇입니다. 다음 컨텍스트를 바탕으로 사용자의 질문에 답변해주세요.
        만약 컨텍스트에 답변이 없다면, "죄송합니다, 관련 정보를 찾을 수 없습니다."라고 답변해주세요.

        컨텍스트:
        {context_list}

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
