# service/chat/chat_graph.py

import boto3
import json
from typing import TypedDict, List, Any

# LangGraph 및 의존성 import
from langgraph.graph import StateGraph, END
from config import settings
from database.repository.chat_repository import ChatRepository
from database.repository.company_repository import CompanyRepository # 오타 수정 및 import
from exception.models.exception import ChatException

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


# --- 2. 그래프 관리 클래스 ---
class ChatGraph:
    def __init__(self, chat_repository: ChatRepository, company_repository: CompanyRepository):
        self.chat_repository = chat_repository
        self.company_repository = company_repository
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



    # faq_search_node 정의
    def faq_search_node(self, state: GraphState) -> dict:
        """[노드 1] FAQ에서 답변을 검색합니다."""
        print("--- 노드 1: FAQ 검색 ---")
        FAQ_SIMILARITY_THRESHOLD = 0.3 # 기존 ChatService의 임계값
        faq_results = chroma_faq_service.search(
            user_question=state["user_question"],
            company_id=state["company_id"],
            n_results=1
        )
        if faq_results.get('distances') and faq_results['distances'][0]:
            distance = faq_results['distances'][0][0]
            if distance < FAQ_SIMILARITY_THRESHOLD:
                print("DEBUG: FAQ에서 답변을 찾았습니다.")
                metadata = faq_results['metadatas'][0][0]
                faq_id = metadata.get('original_faq_id', metadata.get('faq_id', 'unknown'))
                return {
                    "is_faq_found": True,
                    "final_answer": metadata['answer'],
                    "final_metadata": [{
                        "source": "FAQ",
                        "original_question": faq_results['documents'][0][0],
                        "faq_id": faq_id
                    }]
                }
        print("DEBUG: FAQ에서 적절한 답변을 찾지 못했습니다.")
        return {"is_faq_found": False}

    # rag_retrieve_node 정의
    async def rag_retrieve_node(self, state: GraphState) -> dict:
        """[노드 2] RAG를 위한 문서 청크를 검색합니다."""
        print("--- 노드 2: RAG 문서 검색 ---")
        embedding = self._text_to_embedding(state["user_question"])
        similar_chunks = await self.chat_repository.find_similar_chunks(
            embedding=embedding,
            company_id=state["company_id"]
        )
        context_list = []
        for chunk in similar_chunks:
            context_list.append({
                "doc_id": chunk[0], "chunk_id": chunk[1], "content": chunk[2],
                "page_number": chunk[3], "title": chunk[4]
            })
        return {"similar_chunks": similar_chunks, "context_list": context_list}

    # hil_check_node 정의
    async def hil_check_node(self, state: GraphState) -> dict:
        """[노드 3] HIL 실행 여부를 결정합니다."""
        print("--- 노드 3: HIL 실행 여부 확인 ---")
        
        # company_repository는 self에 있으므로 바로 사용합니다.
        company = await self.company_repository.find_by_company_id(state['company_id'])

        threshold = company.think_level if company else 0.7 

        for chunk in state['similar_chunks']:
            # chat_repository의 쿼리 결과에서 distance는 6번째(인덱스 5) 컬럼입니다.
            if chunk[5] >= threshold:
                print("DEBUG: HIL이 발동되지 않았습니다 (유사도 높은 청크 발견).")
                return {"is_hil_triggered": False}
        
        print("DEBUG: HIL이 발동되었습니다 (유사도 높은 청크 없음).")
        return {"is_hil_triggered": True}

    # generate_hil_response_node 정의
    def generate_hil_response_node(self, state: GraphState) -> dict:
        """[노드 4-A] HIL 응답을 생성합니다."""
        print("--- 노드 4-A: HIL 응답 생성 ---")
        metadata = state["context_list"]
        ans_list = [{"문서 제목": data['title'], "문서 페이지": data['page_number']} for data in metadata]
        
        answer = "검색결과가 없습니다. 유사한 문서는 아래의 부분입니다. 만약 해당 부분에서도 원하시는 정보가 없을 시 FAQ에 문의해주세요."
        return {"final_answer": answer, "final_metadata": ans_list}

    # generate_llm_answer_node 정의
    def generate_llm_answer_node(self, state: GraphState) -> dict:
        """[노드 4-B] LLM을 통해 답변을 생성합니다."""
        print("--- 노드 4-B: LLM 답변 생성 ---")
        prompt = f"""
        당신은 사내 문서 검색 챗봇입니다. 다음 컨텍스트를 바탕으로 사용자의 질문에 답변해주세요.
        만약 컨텍스트에 답변이 없다면, "죄송합니다, 관련 정보를 찾을 수 없습니다."라고 답변해주세요.
        컨텍스트: {state['context_list']}
        사용자 질문: {state['user_question']}
        답변:
        """
        try:
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
            body = json.dumps({"anthropic_version": "bedrock-2023-05-31", "max_tokens": 1024, "messages": messages})
            response = self.bedrock_runtime.invoke_model(
                body=body, modelId=self.llm_model_id, accept="application/json", contentType="application/json"
            )
            response_body = json.loads(response.get("body").read())
            answer = response_body['content'][0]['text']
            
            # 메타데이터 생성
            metadata = [{"source": "Document", "title": chunk[4], "chunk_id": chunk[1]} for chunk in state['similar_chunks']]

            return {"final_answer": answer, "final_metadata": metadata}
        except Exception as e:
            raise ChatException(message=f"챗봇 응답 생성 중 오류 발생: {e}")

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
        return "end" if state['is_faq_found'] else "continue_to_rag"

    def decide_hil_or_generate(self, state: GraphState) -> str:
        """[엣지 2] HIL 발동 여부에 따라 다음 단계를 결정합니다."""
        print("--- 엣지 2: HIL/LLM 분기 ---")
        return "trigger_hil" if state['is_hil_triggered'] else "generate_with_llm"

    # --- 그래프 생성 및 컴파일 ---
    def create_graph(self):
        """그래프의 노드와 엣지를 연결하여 실행 가능한 app을 만듭니다."""
        workflow = StateGraph(GraphState)

        # 노드 추가
        workflow.add_node("faq_search", self.faq_search_node)
        workflow.add_node("rag_retrieve", self.rag_retrieve_node)
        workflow.add_node("hil_check", self.hil_check_node)
        workflow.add_node("generate_hil_response", self.generate_hil_response_node)
        workflow.add_node("generate_llm_answer", self.generate_llm_answer_node)

        # 엣지 연결
        workflow.set_entry_point("faq_search")

        workflow.add_conditional_edges(
            "faq_search",
            self.decide_rag_or_end,
            {"continue_to_rag": "rag_retrieve", "end": END}
        )
        
        workflow.add_edge("rag_retrieve", "hil_check")

        workflow.add_conditional_edges(
            "hil_check",
            self.decide_hil_or_generate,
            {"trigger_hil": "generate_hil_response", "generate_with_llm": "generate_llm_answer"}
        )

        workflow.add_edge("generate_hil_response", END)
        workflow.add_edge("generate_llm_answer", END)

        return workflow.compile()