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
smalltalk_history_cache = TTLCache(maxsize=1000, ttl=600)

class ChatService:
    def __init__(self, chat_repository: ChatRepository, company_repository: CompanyRepository, keyword_repository: KeywordRepository):
        
        chat_graph_manager = ChatGraph(
            chat_repository=chat_repository,
            company_repository=company_repository,
            keyword_repository=keyword_repository
        )
        self.app = chat_graph_manager.create_graph()
        self.chat_repository = chat_repository
        self.company_repository = company_repository
        self.keyword_repository = keyword_repository

    async def send_chat(self, message: str, company_id: int, chat_room_id: int, user_id: int):
        if message.startswith("스몰톡"):
            # 1. send_small_chat의 결과를 변수에 저장합니다.
            smalltalk_answer = await self.send_small_chat(
                message=message.replace("스몰톡", ""),
                chat_room_id=chat_room_id,
                user_id=user_id
            )
            
            # 2. 결과가 None인지 확인하고, None이면 기본 오류 메시지를 설정합니다.
            if smalltalk_answer is None:
                smalltalk_answer = "죄송해요, 지금은 스몰톡 답변을 생성할 수 없어요. 나중에 다시 시도해주세요."

            return chatDTO.ChatResponse(
                answer=smalltalk_answer, # 안전하게 처리된 값을 전달합니다.
                metadata=[]
            )

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
            metadata=final_state['final_metadata'],
            chat_id=final_state['chat_id']
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
        graph_instance = ChatGraph(self.chat_repository, self.company_repository, self.keyword_repository)
        response_dict = graph_instance.generate_llm_answer_node(state_for_generation)
        
        return chatDTO.ChatResponse(
            answer=response_dict['final_answer'],
            metadata=filtered_context # 수정된 부분
        )

    async def send_small_chat(self, message: str, chat_room_id: int, user_id: int):
        """소소한 대화 처리 (대화 기록 기능 추가)"""
        bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION_NAME,
            aws_access_key_id=settings.BEDROCK_ACCESS_KEY_ID,
            aws_secret_access_key=settings.BEDROCK_SECRET_ACCESS_KEY,
        )

        # 1. 현재 채팅방의 이전 대화 기록을 캐시에서 가져옵니다.
        history = smalltalk_history_cache.get(chat_room_id, [])
        
        # 2. 이전 대화 기록을 포함하여 모델에 전달할 메시지 리스트를 구성합니다.
        messages = []
        for turn in history:
            messages.append({"role": "user", "content": [{"type": "text", "text": turn["user"]}]})
            messages.append({"role": "assistant", "content": [{"type": "text", "text": turn["assistant"]}]})
        
        # 현재 사용자의 질문을 추가합니다.
        messages.append({"role": "user", "content": [{"type": "text", "text": message}]})

        body_data = {
            "anthropic_version": "bedrock-2023-05-31",
            "system": prompt,
            "messages": messages, # 수정된 메시지 리스트를 사용합니다.
            "max_tokens": 256
        }

        body = json.dumps(body_data).encode('utf-8')

        try:
            response = bedrock_runtime.invoke_model(
                modelId=settings.BEDROCK_LLM_MODEL_ID,
                body=body,
                contentType="application/json",
                accept="application/json"
            )

            response_body = json.loads(response['body'].read())
            completion_text = response_body['content'][0]['text']

            # 3. 현재 대화를 기록에 추가하고 캐시를 업데이트합니다.
            history.append({"user": message, "assistant": completion_text})
            
            # 너무 길어지지 않도록 최근 5개의 대화만 저장합니다.
            smalltalk_history_cache[chat_room_id] = history[-5:]

            return completion_text

        except Exception as e:
            print(f"Error occurred: {e}")
            return None
        
prompt ="""
너는 친절하고 다정한 대화 상대인 '챗봇'이야.
이름은 '아라'야
일상적인 궁금증을 해결해주고, 가벼운 잡담을 나누는 것을 좋아해.
존댓말을 사용하고, 상대방의 기분을 좋게 해주는 따뜻한 말투로 대화해줘.
너는 상대방의 감정에 공감하고, 때로는 간단한 조언이나 긍정적인 메시지를 전달할 수 있어.

**일상 질문의 예시:**
- 오늘 날씨는 어때?
- 점심 메뉴 추천해줘.
- 기분 좋은 이야기를 해줘.
- 지루할 때 할 수 있는 일은 뭐가 있을까?

**제약 조건:**
- 건강, 법률, 금융과 같은 전문적인 조언은 할 수 없어.
- 모르는 질문에는 "죄송해요, 제가 대답하기 어려운 질문이네요."라고 솔직하게 말해줘.
- 개인 정보나 민감한 주제에 대해서는 대답하지 마
"""
