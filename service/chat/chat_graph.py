import boto3
import json
from konlpy.tag import Okt
from typing import TypedDict, List, Any, Optional
import asyncio
# LangGraph 및 의존성 import
from langgraph.graph import StateGraph, END
from config import settings
from database.models import ChatType
from database.repository.chat_repository import ChatRepository
from database.repository.company_repository import CompanyRepository
from exception.models.exception import ChatException
from database.repository.keyword_repository import KeywordRepository
# 서비스 import
from service.chroma_service import chroma_faq_service


# --- 1. 상태 (State) 정의 ---
class GraphState(TypedDict):
    # 입력
    user_question: str
    company_id: int
    chat_room_id: int
    user_id: int

    # 중간 결과
    is_faq_found: bool
    similar_chunks: List[Any]
    context_list: List[dict]
    is_hil_triggered: bool

    # 최종 결과
    final_answer: str
    final_metadata: List[dict]

    is_re_prompt: bool
    chat_id: Optional[int]

    keywords: List[str]

# --- 2. 그래프 관리 클래스 ---
class ChatGraph:
    def __init__(self, chat_repository: ChatRepository, company_repository: CompanyRepository, keyword_repository: KeywordRepository, stopwords_path='stopwords.txt'):        
        self.chat_repository = chat_repository
        self.company_repository = company_repository
        self.keyword_repository = keyword_repository
        self.stopwords_path = stopwords_path
        self.stopwords = None  # 파일을 로드하는 대신 None으로 초기화

        # Okt 분석기 초기화
        self.okt = Okt()

        try:
            self.bedrock_runtime = boto3.client(
                "bedrock-runtime",
                region_name=settings.BEDROCK_REGION_NAME,
                aws_access_key_id=settings.BEDROCK_ACCESS_KEY_ID,
                aws_secret_access_key=settings.BEDROCK_SECRET_ACCESS_KEY,
            )
            self.embedding_model_id = settings.BEDROCK_EMBEDDING_MODEL_ID
            self.llm_model_id = settings.BEDROCK_LLM_MODEL_ID
        except Exception as e:
            raise RuntimeError(f"AWS Bedrock 클라이언트 초기화 실패: {e}")
        
    def _load_stopwords(self):
        """불용어 사전이 아직 로드되지 않았을 경우에만 파일을 로드합니다."""
        if self.stopwords is not None:
            return
        
        try:
            with open(self.stopwords_path, 'r', encoding='utf-8') as f:
                self.stopwords = set(f.read().splitlines())
            print(f"지연 로딩: 불용어 사전 로드 완료 ({len(self.stopwords)}개)")
        except FileNotFoundError:
            self.stopwords = set()
            print(f"경고: {self.stopwords_path} 파일을 찾을 수 없어, 불용어 사전을 비운 상태로 시작합니다.")
                
    async def _extract_keywords_async(self, text: str) -> list:
        self._load_stopwords()
        loop = asyncio.get_running_loop()
        
        pos_tagged = await loop.run_in_executor(None, self.okt.pos, text, True, True)

        keywords = [
            word for word, pos in pos_tagged 
            if pos == 'Noun' and len(word) > 1 and word not in self.stopwords
        ]
        
        # 최대 2개의 키워드만 반환
        return keywords[:2] if len(keywords) > 2 else keywords
    


    # faq_search_node 정의
    async def _faq_search_logic_async(self, user_question: str, company_id: int):
        """기존 faq_search_node의 로직을 비동기 헬퍼 함수로 분리"""
        loop = asyncio.get_running_loop()
        FAQ_SIMILARITY_THRESHOLD = 0.8
        
        faq_results = await loop.run_in_executor(
            None,
            chroma_faq_service.search,
            user_question,
            company_id,
            1
        )

        if faq_results.get('distances') and faq_results['distances'][0]:
            distance = faq_results['distances'][0][0]
            if distance < FAQ_SIMILARITY_THRESHOLD:
                metadata = faq_results['metadatas'][0][0]
                faq_id = metadata.get('original_faq_id', metadata.get('faq_id', 'unknown'))
                return {
                    "final_answer": metadata['answer'],
                    "final_metadata": [{
                        "source": "FAQ",
                        "original_question": faq_results['documents'][0][0],
                        "faq_id": faq_id
                    }]
                }
        return None # FAQ에서 답변을 못 찾으면 None 반환
    

    # 키워트 추출과 FAQ 검색을 비동기 처리하는 노드
    async def process_initial_query_node(self, state: GraphState) -> dict:
        """[노드 1 - 병렬] FAQ 검색과 키워드 추출을 동시에 실행합니다."""
        print("--- 노드 1 (병렬): FAQ 검색 및 키워드 추출 동시 시작 ---")
        user_question = state["user_question"]
        company_id = state["company_id"]


        faq_search_task = asyncio.create_task(

            self._faq_search_logic_async(user_question, company_id)
        )

        keyword_extraction_task = asyncio.create_task(
            self._extract_keywords_async(user_question)
        )


        faq_results, keywords = await asyncio.gather(
            faq_search_task,
            keyword_extraction_task
        )
        print(f"--- 병렬 작업 완료: FAQ 결과 및 키워드 {keywords} 확보 ---")

        if faq_results:
            return {
                "is_faq_found": True,
                "final_answer": faq_results["final_answer"],
                "final_metadata": faq_results["final_metadata"],
                "keywords": keywords 
            }
        
        # FAQ에서 못 찾았을 경우
        return {
            "is_faq_found": False,
            "keywords": keywords
        }


    # rag_retrieve_node 정의
    async def rag_retrieve_node(self, state: GraphState) -> dict:
        """[노드 2 - 수정] 하이브리드 검색을 사용하여 RAG를 위한 문서 청크를 검색합니다."""
        print("--- 노드 2: RAG 문서 검색 (하이브리드) ---")
        user_question = state["user_question"]
        search_query = user_question + " " + " ".join(state.get("keywords", []))
        embedding = self._text_to_embedding(search_query)
        
        # 수정된 find_similar_chunks 호출
        similar_chunks = await self.chat_repository.find_similar_chunks(
            embedding=embedding, 
            company_id=state["company_id"],
            search_query=search_query, # 키워드 검색을 위한 쿼리 전달
            top_k=5 
        )
        
        context_list = [{"doc_id": c[0], "chunk_id": c[1], "content": c[2], "page_number": c[3], "title": c[4]} for c in similar_chunks]
        
        return {"similar_chunks": similar_chunks, "context_list": context_list, "keywords": state.get("keywords", [])}

    # hil_check_node 정의
    async def hil_check_node(self, state: GraphState) -> dict:
        """[노드 3] HIL 실행 여부를 결정합니다."""
        print("--- 노드 3: HIL 실행 여부 확인 ---")
        company = await self.company_repository.find_by_company_id(state['company_id'])
        threshold = (company.think_level * 0.1) if company else 0.7
        is_hil_triggered = True
        for chunk in state['similar_chunks']:
            if chunk[5] >= threshold:
                is_hil_triggered = False
                break
        
        if is_hil_triggered:
            print("DEBUG: HIL이 발동되었습니다.")
        else:
            print("DEBUG: HIL이 발동되지 않았습니다.")
            
        return {"is_hil_triggered": is_hil_triggered, "keywords": state.get("keywords", [])}


    # generate_hil_response_node 정의
    def generate_hil_re_prompt_node(self, state: GraphState) -> dict:
        """
        [노드 5-A] HIL이 발동했을 때, 사용자에게 되물을 질문을 생성합니다.
        """
        print("--- 노드 5-A: HIL 재질문 생성 ---")
        context = state["context_list"]
        
        topics = sorted(list(set([item['title'] for item in context])))
        
        re_prompt_message = (
            "관련성이 높은 답변을 찾지 못했습니다. "
            "대신 아래 주제들에 대한 정보를 드릴 수 있습니다. 어떤 주제에 대해 더 알려드릴까요?\n\n"
            f"선택 가능한 주제: {', '.join(topics)}"
        )
        
        return {"final_answer": re_prompt_message, "final_metadata": context, "is_re_prompt": True, "keywords": state.get("keywords", [])}

    
    # generate_llm_answer_node 정의
    async def generate_llm_answer_node(self, state: GraphState) -> dict:
        """[노드 5-B] LLM을 통해 답변을 생성합니다."""
        print("--- 노드 5-B: LLM 답변 생성 ---")
        prompt = f"""
        당신은 사내 문서 검색 챗봇입니다. 다음 컨텍스트를 바탕으로 사용자의 질문에 답변해주세요.
        만약 컨텍스트에 답변이 없다면, "죄송합니다, 관련 정보를 찾을 수 없습니다."라고 답변해주세요.
        컨텍스트: {state['context_list']}
        사용자 질문: {state['user_question']}
        답변:
        """
        
        try:
            temperature = await self.company_repository.speech_level_find_by_company_id(state.get('company_id')) * 0.1
            
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

            body_data = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": messages,
                "temperature": temperature
            }
            body = json.dumps(body_data)

            response = self.bedrock_runtime.invoke_model(
                body=body, 
                modelId=self.llm_model_id, 
                accept="application/json", 
                contentType="application/json",
                guardrailIdentifier=settings.BEDROCK_GUARDRAIL_ID, 
                guardrailVersion=settings.BEDROCK_GUARDRAIL_VERSION
            )
            response_body = json.loads(response.get("body").read())
            answer = response_body['content'][0]['text']
            
            metadata = [{"source": "Document", "title": chunk[4], "chunk_id": chunk[1], "doc_id": chunk[0]} for chunk in state['similar_chunks']]
        
            return {"final_answer": answer, "final_metadata": metadata, "keywords": state.get("keywords", [])}
        except Exception as e:
            raise ChatException(message=f"챗봇 응답 생성 중 오류 발생: {e}")
        

    async def save_chat_node(self, state: GraphState) -> dict:
        """[수정된 노드] 최종 답변을 Chat 테이블에 저장하고 chat_id를 얻습니다."""
        print("--- 채팅 내용 저장 ---")

        # [로직 수정] FAQ에서 답변을 찾았으면 FAQ 타입, 아니면 일반 DOC 타입으로 지정
        if state.get("is_faq_found", False):
            chat_type = ChatType.FAQ
        else:
            chat_type = ChatType.DOC
        
        faq_id = None
        chunk_ids = []
        # FAQ 답변이 아닐 경우(RAG를 거친 경우)에만 (doc_id, chunk_id)를 저장
        if not state.get("is_faq_found", False):
             chunk_ids=[(item.get("doc_id"), item.get("chunk_id")) for item in state.get("final_metadata", []) if item.get("source") == "Document" and item.get("doc_id") and item.get("chunk_id")]
        else:
            if state.get("final_metadata"):
                faq_id = state["final_metadata"][0].get("faq_id")

        new_chat_id = await self.chat_repository.save_chat(
            question=state["user_question"],
            chat_type=chat_type,
            chat_room_id=state["chat_room_id"],
            user_id=state["user_id"],
            chunk_ids=chunk_ids,
            faq_id=faq_id
        )
        print(f"DEBUG (save_chat_node): DB에서 반환된 new_chat_id: {new_chat_id}")


        return {"chat_id": new_chat_id, "keywords": state.get("keywords", [])}
        
    async def save_keywords_node(self, state: GraphState) -> dict:
        """추출된 키워드를 데이터베이스에 저장합니다."""
        print("--- 최종 노드: 키워드 저장 ---")
        
        # 디버깅을 위해 현재 state의 값을 확인합니다.
        chat_id = state.get("chat_id")
        keywords = state.get("keywords", [])
        print(f"DEBUG (save_keywords_node): chat_id={chat_id}, keywords={keywords}")

        if chat_id and keywords:
            await self.keyword_repository.save_keywords(
                keywords=keywords,
                company_id=state["company_id"],
                chat_id=chat_id
            )
        else:
            print("WARNING: chat_id 또는 keywords가 없어서 저장을 건너뜁니다.")
            
        return {}

    def _text_to_embedding(self, text: str) -> list:
        """텍스트를 임베딩으로 변환하는 헬퍼 함수"""
        try:
            body = json.dumps({"inputText": text})
            response = self.bedrock_runtime.invoke_model(
                body=body, modelId=self.embedding_model_id, accept="application/json", contentType="application/json"
            )
            response_body = json.loads(response.get("body").read())
            embedding = response_body.get("embedding")
            if not embedding:
                raise ChatException(message="임베딩 생성 실패: 응답에 임베딩이 없습니다.")
            return embedding
        except Exception as e:
            raise ChatException(message=f"임베딩 생성 중 오류 발생: {e}")
            
    # --- 엣지 (Edge) 정의 ---

    def decide_rag_or_end(self, state: GraphState) -> str:
        """[엣지 1] FAQ 검색 결과에 따라 다음 단계를 결정합니다."""
        print("--- 엣지 1: FAQ 결과 분기 ---")
        # FAQ 답변을 찾았으면 'save_chat'으로 바로 가서 저장 후 종료
        return "save_chat" if state['is_faq_found'] else "continue_to_rag"

    def decide_hil_or_generate(self, state: GraphState) -> str:
        """[엣지 2] HIL 발동 여부에 따라 다음 단계를 결정합니다."""
        print("--- 엣지 2: HIL/LLM 분기 ---")
        return "trigger_hil" if state['is_hil_triggered'] else "generate_with_llm"

    # --- 그래프 생성 및 컴파일 ---
    def create_graph(self):
        workflow = StateGraph(GraphState)

        # 노드 추가
        workflow.add_node("process_initial_query", self.process_initial_query_node)
        workflow.add_node("rag_retrieve", self.rag_retrieve_node)
        workflow.add_node("hil_check", self.hil_check_node)
        workflow.add_node("generate_hil_re_prompt", self.generate_hil_re_prompt_node)
        workflow.add_node("generate_llm_answer", self.generate_llm_answer_node)
        workflow.add_node("save_chat", self.save_chat_node)
        workflow.add_node("save_keywords", self.save_keywords_node)

        # 엣지 연결
        workflow.set_entry_point("process_initial_query")

        workflow.add_conditional_edges(
            "process_initial_query",
            self.decide_rag_or_end,
            {"continue_to_rag": "rag_retrieve", "save_chat": "save_chat"} 
        )
        
        workflow.add_edge("rag_retrieve", "hil_check")

        workflow.add_conditional_edges(
            "hil_check",
            self.decide_hil_or_generate,
            {"trigger_hil": "generate_hil_re_prompt", "generate_with_llm": "generate_llm_answer"}
        )

        # HIL 재질문은 저장하지 않고 바로 종료, LLM 답변만 저장
        workflow.add_edge("generate_hil_re_prompt", END)  # HIL은 저장 안함
        workflow.add_edge("generate_llm_answer", "save_chat")
        
        # 채팅 저장 후, 키워드 저장 노드로 연결
        workflow.add_edge("save_chat", "save_keywords")
        
        # 키워드 저장 후 최종 종료
        workflow.add_edge("save_keywords", END)

        return workflow.compile()