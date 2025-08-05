import boto3
import chromadb
import json
from chromadb import Documents, EmbeddingFunction, Embeddings

from config import settings
from exception.models.exception import FaqException, AIException


class BedrockEmbeddingFunction(EmbeddingFunction):
    def __init__(self, bedrock_runtime, model_id: str):
        """
        Bedrock 클라이언트와 모델 ID로 초기화합니다.
        """
        self.bedrock_runtime = bedrock_runtime
        self.model_id = model_id

    def __call__(self, input: Documents) -> Embeddings:
        """
        ChromaDB가 텍스트 목록(input)을 주면, Bedrock API를 호출하여
        임베딩 목록을 반환합니다.
        """
        embeddings = []
        for text in input:
            try:
                # Bedrock Titan V2 모델의 요청 본문 형식
                body = json.dumps({"inputText": text})
                response = self.bedrock_runtime.invoke_model(
                    body=body,
                    modelId=self.model_id,
                    accept="application/json",
                    contentType="application/json"
                )
                response_body = json.loads(response.get("body").read())
                embedding = response_body.get("embedding")
                if embedding:
                    embeddings.append(embedding)
                else:
                    # 임베딩 생성 실패 시 오류 발생
                    raise AIException(message="Failed to get embedding for text(chroma)")
            except Exception as e:
                print(f"Error creating embedding for text '{text[:100]}...': {e}")
                raise AIException(message="Failed to get embedding for text(chroma)")
        return embeddings

class ChromaFAQService:
    def __init__(self, path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=path)
        
        try:
            # Bedrock 클라이언트 초기화
            bedrock_runtime = boto3.client(
                service_name="bedrock-runtime",
                region_name=settings.BEDROCK_REGION_NAME,
                aws_access_key_id=settings.BEDROCK_ACCESS_KEY_ID,
                aws_secret_access_key=settings.BEDROCK_SECRET_ACCESS_KEY
            )
        except Exception as e:
            print(f"Error initializing AWS Bedrock client: {e}")
            raise AIException(message="Failed to initialize AWS Bedrock client.")

        # 위에서 정의한 커스텀 클래스의 인스턴스 생성
        bedrock_ef = BedrockEmbeddingFunction(
            bedrock_runtime=bedrock_runtime,
            model_id=settings.BEDROCK_EMBEDDING_MODEL_ID
        )
        
        # 컬렉션을 가져올 때 커스텀 임베딩 함수를 지정
        self.collection = self.client.get_or_create_collection(
            name="faq",
            embedding_function=bedrock_ef 
        )
        
        print("ChromaDB FAQ Service Initialized with AWS Bedrock Titan Embedding Model.")


    def upsert_faq(self, faq_id: int, question: str, answer: str, company_id: int, tag_id: int):
        """FAQ를 ChromaDB에 추가하거나 업데이트합니다. (Upsert)"""
        try:
            self.collection.upsert(
                ids=[f"faq_{faq_id}"],
                documents=[question],
                metadatas=[
                    {
                        "answer": answer,
                        "original_faq_id": faq_id,
                        "company_id": company_id,
                        "tag_id": tag_id
                    }
                ]
            )
            print(f"Upserted FAQ {faq_id} to ChromaDB.")
        except Exception as e:

            print(f"Error upserting FAQ {faq_id} to ChromaDB: {e}")
            raise FaqException(message="FAQ upsert failed. Please try again later.")


    def delete_faq(self, faq_id: int):
        """ChromaDB에서 FAQ를 삭제합니다."""
        try:
            self.collection.delete(ids=[f"faq_{faq_id}"])
            print(f"Deleted FAQ {faq_id} from ChromaDB.")
        except Exception as e:
            print(f"Error deleting FAQ {faq_id} from ChromaDB: {e}")
            raise FaqException(message="FAQ deletion failed.")

    def search(self, user_question: str, company_id: int, n_results: int = 1):
        """사용자 질문으로 ChromaDB에서 가장 유사한 FAQ를 검색합니다."""
        results = self.collection.query(
            query_texts=[user_question],
            n_results=n_results,
            where={"company_id": company_id} 
        )
        return results
    
    

# 서비스 인스턴스를 싱글톤처럼 생성하여 사용
chroma_faq_service = ChromaFAQService()