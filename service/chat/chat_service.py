import boto3
import json

from api.routes.chat import chatDTO
from config import settings
from database.repository.chat_repository import ChatRepository
from service.chat import HIL_service
from service.chroma_service import chroma_faq_service
from exception.models.exception import ChatException

class ChatService:
    def __init__(self, chat_repository: ChatRepository):
        self.chat_repository = chat_repository

        try:
            # AWS Bedrock 클라이언트 설정
            self.bedrock_runtime = boto3.client(
                service_name="bedrock-runtime",
                region_name=settings.AWS_REGION_NAME,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            # 설정에서 Bedrock 모델 ID 가져오기
            self.embedding_model_id = settings.BEDROCK_EMBEDDING_MODEL_ID
            self.llm_model_id = settings.BEDROCK_LLM_MODEL_ID
        except Exception as e:
            raise RuntimeError(f"AWS Bedrock 클라이언트 초기화 실패: {e}")

        # ChromaDB 서비스는 그대로 사용
        self.chroma_service = chroma_faq_service

    async def send_chat(self, message: str, company_id: int, chat_room_id: int, user_id: int) -> chatDTO.ChatResponse:
        
        #FAQ 로직
        FAQ_SIMILARITY_THRESHOLD = 0.9
        
        faq_results = self.chroma_service.search(
            user_question=message,
            company_id=company_id,
            n_results=1
        )
        
        if faq_results.get('distances') and faq_results['distances'][0]:
            distance = faq_results['distances'][0][0]
            print(f"DEBUG: FAQ Distance: {distance}")
            
            # 가장 유사한 결과의 유사도(거리)가 임계값보다 낮은 경우
            if distance < FAQ_SIMILARITY_THRESHOLD:
                print("DEBUG: FAQ에서 답변을 찾았습니다.")
                faq_answer = faq_results['metadatas'][0][0]['answer']
                # original_faq_id 안전하게 가져오기
                metadata = faq_results['metadatas'][0][0]
                faq_id = metadata.get('original_faq_id', metadata.get('faq_id', 'unknown'))
                
                faq_metadata = [{
                    "source": "FAQ",
                    "original_question": faq_results['documents'][0][0],
                    "faq_id": faq_id
                }]
                
                # FAQ 답변을 즉시 반환하고 함수 종료
                return chatDTO.ChatResponse(
                    answer=faq_answer,
                    metadata=faq_metadata
                )
            
        # RAG 로직
        print("DEBUG: FAQ에서 적절한 답변을 찾지 못해 RAG를 실행합니다.")
        
        embedding = self._text_to_embedding(message)
        similar_chunks = await self.chat_repository.find_similar_chunks(
        embedding=embedding, 
        company_id=company_id
    )

        context_list = []
        for chunk in similar_chunks:
            try:
                chunk_dict = {

                    "doc_id": chunk[0],      # doc_id
                    "chunk_id": chunk[1],    # chunk_id
                    "title": chunk[4],       # title
                    "page_number": chunk[3], # page_number
                    "content": chunk[2],     # content
                }
                context_list.append(chunk_dict)
            except (AttributeError, IndexError):
                raise ChatException(message="청크 데이터 형식이 올바르지 않습니다. 청크 데이터를 확인해주세요.")
            except Exception as e:
                raise ChatException(message=f"청크 처리 중 오류 발생: {e}")


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

        try:
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": messages
            })

            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.llm_model_id, 
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get("body").read())
            answer = response_body['content'][0]['text']

        except Exception as e:
            raise ChatException(message=f"챗봇 응답 생성 중 오류 발생: {e}")

        metadata = [
        {
            "source": "Document",
            "title": chunk.title,  
            "chunk_id": chunk.chunk_id 
        }
        for chunk in similar_chunks
        ]


        return chatDTO.ChatResponse(
            answer=answer,
            metadata=metadata
        )

    def _text_to_embedding(self, text: str) -> list:
        """
        텍스트를 AWS Bedrock의 'Titan Text Embeddings V2' 모델을 사용하여 벡터로 변환합니다.
        """
        try:
            # Titan V2 모델의 요청 본문 형식
            body = json.dumps({
                "inputText": text,
                # "dimensions": 1024 # 필요시 임베딩 차원 지정 (기본값: 1024)
            })


            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.embedding_model_id,
                accept="application/json",
                contentType="application/json"
            )
            
    
            response_body = json.loads(response.get("body").read())
            embedding = response_body.get("embedding")
            
            if not embedding:
                raise ChatException(message="임베딩 생성 실패: 응답에 임베딩이 없습니다.")

            return embedding
        except Exception as e:
            raise ChatException(message=f"임베딩 생성 중 오류 발생: {e}")