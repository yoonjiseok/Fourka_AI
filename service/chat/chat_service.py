import json

import boto3
from cachetools import TTLCache

from api.routes.chat import chatDTO
from config import settings
from database.repository.chat_repository import ChatRepository
from database.repository.company_repository import CompanyRepository
from database.repository.keyword_repository import KeywordRepository
from .chat_graph import ChatGraph  # 위에서 만든 클래스 import

# 채팅방별로 HIL 컨텍스트를 10분간 저장하는 캐시
hil_context_cache = TTLCache(maxsize=1000, ttl=600)

class ChatService:
    def __init__(self, chat_repository: ChatRepository, company_repository: CompanyRepository, keyword_repository: KeywordRepository):
        
        chat_graph_manager = ChatGraph(
            chat_repository=chat_repository,
            company_repository=company_repository,
            keyword_repository=keyword_repository
        )
        self.app = chat_graph_manager.create_graph()

    async def send_chat(self, message: str, company_id: int, chat_room_id: int, user_id: int):
        
        # --- 1. 재질문에 대한 답변인지 확인 ---
        cached_context = hil_context_cache.get(chat_room_id)
        
        if cached_context:
            print(f"DEBUG: HIL 재질문에 대한 답변을 처리합니다. (채팅방 ID: {chat_room_id})")
            # 캐시에서 컨텍스트를 사용했으므로 삭제 (재질문은 한 번만)
            del hil_context_cache[chat_room_id]
            
            # 저장된 컨텍스트와 사용자의 새 메시지로 직접 LLM 답변 생성
            return await self._generate_answer_from_context(message, cached_context)

        # --- 2. 일반적인 첫 질문 처리 ---
        initial_state = {
            "user_question": message,
            "company_id": company_id,
            "chat_room_id": chat_room_id,
            "user_id": user_id,
            "is_re_prompt": False
        }
        
        final_state = await self.app.ainvoke(initial_state)

        # --- 3. 그래프 결과에 따른 후처리 ---
        # 만약 그래프가 재질문이 필요하다고 응답했다면,
        if final_state.get("is_re_prompt"):
            print(f"DEBUG: HIL 재질문이 필요합니다. 컨텍스트를 캐시에 저장합니다. (채팅방 ID: {chat_room_id})")
            # 다음 턴에서 사용할 컨텍스트(final_metadata)를 캐시에 저장
            hil_context_cache[chat_room_id] = final_state["final_metadata"]

        return chatDTO.ChatResponse(
            answer=final_state['final_answer'],
            metadata=final_state['final_metadata']
        )

    async def _generate_answer_from_context(self, user_choice: str, context: list[dict]):
        """HIL 재질문 답변을 처리하기 위한 별도 로직"""
        
        # 사용자가 선택한 주제와 관련된 내용만 필터링
        filtered_context = [
            item for item in context if user_choice.lower() in item.get('title', '').lower()
        ]

        if not filtered_context:
            
            return chatDTO.ChatResponse(answer="선택지에 없는 주제입니다. 다시 질문해주세요.", metadata=[])

        state_for_generation = {
            "context_list": filtered_context,
            "user_question": user_choice,
            "similar_chunks": [] # 이 경우엔 필요 없음
        }
        # ChatGraph의 인스턴스 메서드를 직접 호출
        graph_instance = ChatGraph(self.chat_repository, self.company_repository)
        response_dict = graph_instance.generate_llm_answer_node(state_for_generation)
        
        return chatDTO.ChatResponse(
            answer=response_dict['final_answer'],
            metadata=response_dict['final_metadata']
        )

    async def send_small_chat(self, message: str):
        """소소한 대화 처리"""
        bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION_NAME,
            aws_access_key_id=settings.BEDROCK_ACCESS_KEY_ID,
            aws_secret_access_key=settings.BEDROCK_SECRET_ACCESS_KEY,
        )

        # 1. 모델이 요구하는 JSON 형식으로 본문(body) 구성
        # Claude 3 모델의 경우 "messages" 형식을 사용합니다.
        body_data = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": message}]
                }
            ],
            "max_tokens": 512
        }

        # 2. JSON을 문자열로 변환하고 바이트로 인코딩
        body = json.dumps(body_data).encode('utf-8')

        try:
            response = bedrock_runtime.invoke_model(
                modelId=settings.BEDROCK_LLM_MODEL_ID,
                body=body,
                contentType="application/json",
                accept="application/json"
            )

            # 3. 응답 본문(body) 읽기 및 파싱
            # StreamingBody 객체를 읽고 JSON으로 디코딩합니다.
            response_body = json.loads(response['body'].read())

            # 4. 응답 텍스트 추출 (Claude 3 모델 기준)
            completion_text = response_body['content'][0]['text']

            return completion_text

        except Exception as e:
            print(f"Error occurred: {e}")
            return None