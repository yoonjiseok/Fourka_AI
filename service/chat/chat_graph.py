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
from database.repository.company_repository import CompanyRepository # 오타 수정 및 import
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
    def __init__(self, chat_repository: ChatRepository, company_repository: CompanyRepository, keyword_repository: KeywordRepository):
        self.chat_repository = chat_repository
        self.company_repository = company_repository
        self.keyword_repository = keyword_repository
        
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
        
    async def _extract_keywords_async(self, text: str) -> list:
        loop = asyncio.get_running_loop()
        # self.okt.nouns 라는 동기 함수를 별도의 스레드에서 실행시켜 비동기 이벤트 루프를 막지 않게 함
        nouns = await loop.run_in_executor(None, self.okt.nouns, text)
        
        # 불용어 처리 로직은 여기에 그대로 적용
        stopwords = set([
            "가", "가까스로", "가령", "각", "각각", "각자", "각종", "갖고말하자면", "같다", "같이", "개의치않고", "거니와", "거바", "거의", "것", "것과 같이", "것들", "게다가", "게우다", "겨우", "견지에서", "결과에 이르다", "결국", "결론을 낼 수 있다", "겸사겸사", "고려하면", "고로", "곧", "공동으로", "과", "과연", "관계가 있다", "관계없이", "관련이 있다", "관하여", "관한", "관해서는", "구", "구체적으로", "구토하다", "그", "그들", "그때", "그래", "그래도", "그래서", "그러나", "그러니", "그러니까", "그러면", "그러므로", "그러한즉", "그런 까닭에", "그런데", "그런즉", "그럼", "그럼에도 불구하고", "그렇게 함으로써", "그렇지", "그렇지 않다면", "그렇지 않으면", "그렇지만", "그렇지않으면", "그리고", "그리하여", "그만이다", "그에 따르는", "그위에", "그저", "그중에서", "그치지 않다", "근거로", "근거하여", "기대여", "기점으로", "기준으로", "기타", "까닭으로", "까악", "까지", "까지 미치다", "까지도", "꽈당", "끙끙", "끼익", 
            "나", "나머지는", "남들", "남짓", "너", "너희", "너희들", "네", "넷", "년", "논하지 않다", "놀라다", "누가 알겠는가", "누구", 
            "다른", "다른 방면으로", "다만", "다섯", "다소", "다수", "다시 말하자면", "다시말하면", "다음", "다음에", "다음으로", "단지", "답다", "당신", "당장", "대로 하다", "대하면", "대하여", "대해 말하자면", "대해서", "댕그", "더구나", "더군다나", "더라도", "더불어", "더욱더", "더욱이는", "도달하다", "도착하다", "동시에", "동안", "된바에야", "된이상", "두번째로", "둘", "둥둥", "뒤따라", "뒤이어", "든간에", "들", "등", "등등", "딩동", "따라", "따라서", "따위", "따지지 않다", "딱", "때", "때가 되어", "때문에", "또", "또한", "뚝뚝", 
            "라 해도", "령", "로", "로 인하여", "로부터", "로써", "륙", "를", 
            "마음대로", "마저", "마저도", "마치", "막론하고", "만 못하다", "만약", "만약에", "만은 아니다", "만이 아니다", "만일", "만큼", "말하자면", "말할것도 없고", "매", "매번", "메쓰겁다", "몇", "모", "모두", "무렵", "무릎쓰고", "무슨", "무엇", "무엇때문에", "물론", "및", 
            "바꾸어말하면", "바꾸어말하자면", "바꾸어서 말하면", "바꾸어서 한다면", "바꿔 말하면", "바로", "바와같이", "밖에 안된다", "반대로", "반대로 말하자면", "반드시", "버금", "보는데서", "보다더", "보드득", "본대로", "봐", "봐라", "부류의 사람들", "부터", "불구하고", "불문하고", "붕붕", "비걱거리다", "비교적", "비길수 없다", "비로소", "비록", "비슷하다", "비추어 보아", "비하면", "뿐만 아니라", "뿐만아니라", "뿐이다", "삐걱", "삐걱거리다", 
            "사", "삼", "상대적으로 말하자면", "생각한대로", "설령", "설마", "설사", "셋", "소생", "소인", "솨", "쉿", "습니까", "습니다", "시각", "시간", "시작하여", "시초에", "시키다", "실로", "심지어", 
            "아", "아니", "아니나다를가", "아니라면", "아니면", "아니었다면", "아래윗", "아무거나", "아무도", "아야", "아울러", "아이", "아이고", "아이구", "아이야", "아이쿠", "아하", "아홉", "안 그러면", "않기 위하여", "않기 위해서", "알 수 있다", "알았어", "앗", "앞에서", "앞의것", "야", "약간", "양자", "어", "어기여차", "어느", "어느 년도", "어느것", "어느곳", "어느때", "어느쪽", "어느해", "어디", "어때", "어떠한", "어떤", "어떤것", "어떤것들", "어떻게", "어떻해", "어이", "어째서", "어쨋든", "어쩌라고", "어쩌면", "어쩌면 해도", "어쩌다", "어쩔수 없다", "어찌", "어찌됏든", "어찌됏어", "어찌하든지", "어찌하여", "언제", "언젠가", "얼마", "얼마 안 되는 것", "얼마간", "얼마나", "얼마든지", "얼마만큼", "얼마큼", "엉엉", "에", "에 가서", "에 달려 있다", "에 대해", "에 있다", "에 한하다", "에게", "에서", "여", "여기", "여덟", "여러분", "여보시오", "여부", "여섯", "여전히", "여차", "연관되다", "연이서", "영", "영차", "옆사람", "예", "예를 들면", "예를 들자면", "예컨대", "예하면", "오", "오로지", "오르다", "오자마자", "오직", "오호", "오히려", "와", "와 같은 사람들", "와르르", "와아", "왜", "왜냐하면", "외에도", "요만큼", "요만한 것", "요만한걸", "요컨대", "우르르", "우리", "우리들", "우선", "우에 종합한것과같이", "운운", "월", "위에서 서술한바와같이", "위하여", "위해서", "윙윙", "육", "으로", "으로 인하여", "으로서", "으로써", "을", "응", "응당", "의", "의거하여", "의지하여", "의해", "의해되다", "의해서", "이", "이 되다", "이 때문에", "이 밖에", "이 외에", "이 정도의", "이것", "이곳", "이때", "이라면", "이래", "이러이러하다", "이러한", "이런", "이럴정도로", "이렇게 많은 것", "이렇게되면", "이렇게말하면", "이렇구나", "이로 인하여", "이르기까지", "이리하여", "이만큼", "이번", "이봐", "이상", "이어서", "이었다", "이와 같다", "이와 같은", "이와 반대로", "이와같다면", "이외에도", "이용하여", "이유만으로", "이젠", "이지만", "이쪽", "이천구", "이천육", "이천칠", "이천팔", "인 듯하다", "인젠", "일", "일것이다", "일곱", "일단", "일때", "일반적으로", "일지라도", "임에 틀림없다", "입각하여", "입장에서", "잇따라", "있다", 
            "자", "자기", "자기집", "자마자", "자신", "잠깐", "잠시", "저", "저것", "저것만큼", "저기", "저쪽", "저희", "전부", "전자", "전후", "점에서 보아", "정도에 이르다", "제", "제각기", "제외하고", "조금", "조차", "조차도", "졸졸", "좀", "좋아", "좍좍", "주룩주룩", "주저하지 않고", "줄은 몰랏다", "줄은모른다", "중에서", "중의하나", "즈음하여", "즉", "즉시", "지든지", "지만", "지말고", "진짜로", "쪽으로", 
            "차라리", "참", "참나", "첫번째로", "쳇", "총적으로", "총적으로 말하면", "총적으로 보면", "칠", 
            "콸콸", "쾅쾅", "쿵", 
            "타다", "타인", "탕탕", "토하다", "통하여", "툭", "퉤", "틈타", 
            "팍", "팔", "퍽", "펄렁", 
            "하", "하게될것이다", "하게하다", "하겠는가", "하고 있다", "하고있었다", "하곤하였다", "하구나", "하기 때문에", "하기 위하여", "하기는한데", "하기만 하면", "하기보다는", "하기에", "하나", "하느니", "하는 김에", "하는 편이 낫다", "하는것도", "하는것만 못하다", "하는것이 낫다", "하는바", "하더라도", "하도다", "하도록시키다", "하도록하다", "하든지", "하려고하다", "하마터면", "하면 할수록", "하면된다", "하면서", "하물며", "하여금", "하여야", "하자마자", "하지 않는다면", "하지 않도록", "하지마", "하지마라", "하지만", "하하", "한 까닭에", "한 이유는", "한 후", "한다면", "한다면 몰라도", "한데", "한마디", "한적이있다", "한켠으로는", "한항목", "할 따름이다", "할 생각이다", "할 줄 안다", "할 지경이다", "할 힘이 있다", "할때", "할만하다", "할망정", "할뿐", "할수있다", "할수있어", "할줄알다", "할지라도", "할지언정", "함께", "해도된다", "해도좋다", "해봐요", "해서는 안된다", "해야한다", "해요", "했어요", "향하다", "향하여", "향해서", "허", "허걱", "허허", "헉", "헉헉", "헐떡헐떡", "형식으로 쓰여", "혹시", "혹은", "혼자", "훨씬", "휘익", "휴", "흐흐", "흥", "힘입어"

        ])
        keywords = [word for word in nouns if word not in stopwords and len(word) > 1]
        
        if len(keywords) > 2:
            return keywords[:2]
        return keywords    
    


    # faq_search_node 정의
    async def _faq_search_logic_async(self, user_question: str, company_id: int):
        """기존 faq_search_node의 로직을 비동기 헬퍼 함수로 분리"""
        loop = asyncio.get_running_loop()
        FAQ_SIMILARITY_THRESHOLD = 0.5
        
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
        """[노드 2] RAG를 위한 문서 청크를 검색합니다."""
        print("--- 노드 2: RAG 문서 검색 ---")
        search_query = state["user_question"] + " " + " ".join(state.get("keywords", []))
        embedding = self._text_to_embedding(search_query)
        similar_chunks = await self.chat_repository.find_similar_chunks(embedding=embedding, company_id=state["company_id"])
        context_list = [{"doc_id": c[0], "chunk_id": c[1], "content": c[2], "page_number": c[3], "title": c[4]} for c in similar_chunks]
        
        return {"similar_chunks": similar_chunks, "context_list": context_list, "keywords": state.get("keywords", [])}

    # hil_check_node 정의
    async def hil_check_node(self, state: GraphState) -> dict:
        """[노드 3] HIL 실행 여부를 결정합니다."""
        print("--- 노드 3: HIL 실행 여부 확인 ---")
        company = await self.company_repository.find_by_company_id(state['company_id'])
        threshold = company.think_level if company else 0.7
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
    def generate_llm_answer_node(self, state: GraphState) -> dict:
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
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
            body = json.dumps({"anthropic_version": "bedrock-2023-05-31", "max_tokens": 1024, "messages": messages})
            response = self.bedrock_runtime.invoke_model(
                body=body, modelId=self.llm_model_id, accept="application/json", contentType="application/json",
                guardrailIdentifier=settings.BEDROCK_GUARDRAIL_ID, guardrailVersion=settings.BEDROCK_GUARDRAIL_VERSION
            )
            response_body = json.loads(response.get("body").read())
            answer = response_body['content'][0]['text']
            
            # 메타데이터 생성
            metadata = [{"source": "Document", "title": chunk[4], "chunk_id": chunk[1]} for chunk in state['similar_chunks']]
        
            return {"final_answer": answer, "final_metadata": metadata, "keywords": state.get("keywords", [])}
        except Exception as e:
            raise ChatException(message=f"챗봇 응답 생성 중 오류 발생: {e}")
        

    async def save_chat_node(self, state: GraphState) -> dict:
        """[신규 노드] 최종 답변을 Chat 테이블에 저장하고 chat_id를 얻습니다."""
        print("--- 신규 노드: 채팅 내용 저장 ---")

        if state.get("is_faq_found", False):
            chat_type = ChatType.DOC
        else:
            chat_type = ChatType.FAQ

        chunk_ids = []
        if not state.get("is_faq_found", False):
             chunk_ids=[item.get("chunk_id") for item in state.get("final_metadata", []) if item.get("source") == "Document"]

        new_chat_id = await self.chat_repository.save_chat(
            question=state["user_question"],
            chat_type=chat_type,
            chat_room_id=state["chat_room_id"],
            user_id=state["user_id"],
            chunk_ids=chunk_ids
        )
        print(f"DEBUG (save_chat_node): DB에서 반환된 new_chat_id: {new_chat_id}")
        
        # 중요: 다음 노드를 위해 keywords와 새로 생성된 chat_id를 함께 전달합니다.
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
        return "end" if state['is_faq_found'] else "continue_to_rag"

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
            {"continue_to_rag": "rag_retrieve", "end": "save_chat"} # FAQ 답변 후 채팅 저장
        )
        
        workflow.add_edge("rag_retrieve", "hil_check")

        workflow.add_conditional_edges(
            "hil_check",
            self.decide_hil_or_generate,
            {"trigger_hil": "generate_hil_re_prompt", "generate_with_llm": "generate_llm_answer"}
        )

        # 답변 생성 후, 채팅 저장 노드로 연결
        workflow.add_edge("generate_hil_re_prompt", "save_chat")
        workflow.add_edge("generate_llm_answer", "save_chat")
        
        # 채팅 저장 후, 키워드 저장 노드로 연결
        workflow.add_edge("save_chat", "save_keywords")
        
        # 키워드 저장 후 최종 종료
        workflow.add_edge("save_keywords", END)

        return workflow.compile()