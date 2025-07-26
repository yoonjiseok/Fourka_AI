import chromadb
from config import settings
from chromadb.utils import embedding_functions
class ChromaFAQService:
    def __init__(self, path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=path)
        
        gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=settings.GEMINI_API_KEY,
            model_name="models/embedding-001"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="faq",
            embedding_function=gemini_ef 
        )
        
        print("ChromaDB FAQ Service Initialized with Gemini Embedding Model.")

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


    def delete_faq(self, faq_id: int):
        """ChromaDB에서 FAQ를 삭제합니다."""
        try:
            self.collection.delete(ids=[f"faq_{faq_id}"])
            print(f"Deleted FAQ {faq_id} from ChromaDB.")
        except Exception as e:
            print(f"Error deleting FAQ {faq_id} from ChromaDB: {e}")

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