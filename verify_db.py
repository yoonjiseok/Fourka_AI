import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

async def verify_database():
    db_url = os.getenv('DB_URL').replace('postgresql+asyncpg://', 'postgresql://')
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # chunk 테이블 구조 확인
        print("📋 현재 chunk 테이블 구조:")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'chunk'
            ORDER BY ordinal_position;
        """)
        
        has_weight = False
        has_updated_at = False
        
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (default: {col['column_default']})")
            if col['column_name'] == 'weight':
                has_weight = True
            if col['column_name'] == 'updated_at':
                has_updated_at = True
        
        # 결과 판정
        print(f"\n✅ weight 컬럼: {'있음' if has_weight else '❌ 없음'}")
        print(f"✅ updated_at 컬럼: {'있음' if has_updated_at else '❌ 없음'}")
        
        # alembic_version 확인
        alembic_version = await conn.fetchrow("SELECT version_num FROM alembic_version;")
        print(f"📋 alembic 버전: {alembic_version['version_num']}")
        
        await conn.close()
        
        if has_weight and has_updated_at:
            print("\n🎉 모든 컬럼이 올바르게 존재합니다! Alembic이 제대로 작동하고 있어요.")
        else:
            print("\n❌ 일부 컬럼이 누락되었습니다. Alembic에 문제가 있을 수 있어요.")
        
    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    asyncio.run(verify_database()) 