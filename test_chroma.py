import chromadb
from config import settings # 기존에 사용하시던 설정 파일을 그대로 임포트합니다.

def check_chroma_db():
    # 1. 원격 ChromaDB 서버에 연결
    print(f"Connecting to ChromaDB at {settings.CHROMA_DB_URL}...")
    try:
        host, port = settings.CHROMA_DB_URL.split(":")
        client = chromadb.HttpClient(host=host, port=int(port))
        print("✅ Connection successful!")
    except Exception as e:
        print(f"🔥 Connection failed: {e}")
        return

    # 2. 모든 컬렉션 목록 가져오기
    collections = client.list_collections()
    print(f"\nFound {len(collections)} collections:")
    for collection in collections:
        print(f"- {collection.name}")

    # 3. 'faq' 컬렉션 데이터 확인
    try:
        # 'faq' 컬렉션을 객체로 가져오기
        faq_collection = client.get_collection("faq")
        
        # 컬렉션에 있는 아이템 총 개수 확인
        count = faq_collection.count()
        print(f"\n🔍 Checking 'faq' collection... It has {count} items.")
        
        if count > 0:
            # 컬렉션의 모든 데이터 가져오기 (limit을 조절해 가져올 개수 제한 가능)
            # include 인자에 따라 documents, metadatas, embeddings를 선택적으로 가져올 수 있습니다.
            all_data = faq_collection.get(
                limit=10, # 우선 10개만 가져오도록 제한
                include=["metadatas", "documents"] 
            )
            
            print("\n--- First 10 items in 'faq' collection ---")
            for i in range(len(all_data['ids'])):
                print(f"ID: {all_data['ids'][i]}")
                print(f"  Document (Question): {all_data['documents'][i]}")
                print(f"  Metadata (Answer etc.): {all_data['metadatas'][i]}")
                print("-" * 20)
                
    except Exception as e:
        print(f"🔥 Error getting 'faq' collection data: {e}")


if __name__ == "__main__":
    check_chroma_db()