#!/usr/bin/env python3
"""
피드백 알림 기능 테스트 스크립트
Redis Stream에 알림이 정상적으로 발행되는지 확인합니다.
"""

import asyncio
import requests
import redis.asyncio as async_redis
from datetime import datetime
import json

# 설정
FASTAPI_BASE_URL = "http://localhost:8000"  # FastAPI 서버 주소
REDIS_URL = "redis://localhost:6379"  # Redis 서버 주소

async def test_feedback_notification():
    """피드백 생성 및 Redis Stream 알림 테스트"""
    
    print("🚀 피드백 알림 테스트 시작")
    print("=" * 50)
    
    # Redis 클라이언트 연결
    redis_client = async_redis.from_url(REDIS_URL, decode_responses=True)
    
    try:
        # 1. Redis 연결 테스트
        print("1️⃣ Redis 연결 테스트...")
        await redis_client.ping()
        print("✅ Redis 연결 성공")
        
        # 2. 스트림 이전 상태 확인
        print("\n2️⃣ 기존 스트림 확인...")
        try:
            stream_info = await redis_client.xinfo_stream("notification-stream")
            print(f"📊 기존 메시지 수: {stream_info['length']}")
        except Exception:
            print("📊 기존 스트림 없음 (첫 번째 메시지가 될 예정)")
        
        # 3. 피드백 생성 API 호출
        print("\n3️⃣ 피드백 생성 API 호출...")
        feedback_data = {
            "chat_id": 28,  # 실제 존재하는 chat_id
            "feedback_type": "UNLIKE",
            "feedback_reason": "WRONG_ANSWER",
            "feedback_content": "테스트용 피드백입니다",
            "answer": "테스트 답변"
        }
        
        response = requests.post(
            f"{FASTAPI_BASE_URL}/api/ai/feedbacks/create",
            json=feedback_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ 피드백 생성 성공")
            print(f"📄 응답: {response.json()}")
        else:
            print(f"❌ 피드백 생성 실패: {response.status_code}")
            print(f"📄 에러: {response.text}")
            return
        
        # 4. Redis Stream에서 새 메시지 확인
        print("\n4️⃣ Redis Stream 메시지 확인...")
        await asyncio.sleep(1)  # 메시지 발행 대기
        
        # 최근 메시지 조회
        messages = await redis_client.xread({"notification-stream": "$"}, count=1, block=2000)
        
        if messages:
            stream_name, stream_messages = messages[0]
            print(f"✅ 새 알림 메시지 수신: {len(stream_messages)}개")
            
            for msg_id, fields in stream_messages:
                print(f"📨 메시지 ID: {msg_id}")
                print(f"📋 메시지 내용:")
                for field, value in fields.items():
                    print(f"   - {field}: {value}")
        else:
            # 전체 스트림에서 마지막 메시지 확인
            print("⏱️ 실시간 메시지 없음, 전체 스트림에서 최근 메시지 확인...")
            all_messages = await redis_client.xread({"notification-stream": "0"}, count=1)
            if all_messages:
                stream_name, stream_messages = all_messages[0]
                if stream_messages:
                    msg_id, fields = stream_messages[-1]  # 마지막 메시지
                    print(f"📨 최근 메시지 ID: {msg_id}")
                    print(f"📋 메시지 내용:")
                    for field, value in fields.items():
                        print(f"   - {field}: {value}")
        
        # 5. 스트림 전체 상태 확인
        print("\n5️⃣ 최종 스트림 상태...")
        stream_info = await redis_client.xinfo_stream("notification-stream")
        print(f"📊 총 메시지 수: {stream_info['length']}")
        print(f"📊 마지막 메시지 ID: {stream_info['last-generated-id']}")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
    
    finally:
        await redis_client.aclose()
        print("\n🏁 테스트 완료")

async def read_stream_messages():
    """Redis Stream의 모든 메시지를 읽어보는 함수"""
    print("📖 Redis Stream 메시지 읽기")
    print("=" * 30)
    
    redis_client = async_redis.from_url(REDIS_URL, decode_responses=True)
    
    try:
        messages = await redis_client.xrange("notification-stream")
        
        if not messages:
            print("📭 스트림에 메시지가 없습니다")
            return
        
        print(f"📨 총 {len(messages)}개의 메시지 발견")
        print()
        
        for i, (msg_id, fields) in enumerate(messages, 1):
            print(f"메시지 #{i}")
            print(f"ID: {msg_id}")
            print("내용:")
            for field, value in fields.items():
                print(f"  {field}: {value}")
            print("-" * 30)
    
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    finally:
        await redis_client.aclose()

def main():
    """메인 함수"""
    print("피드백 알림 테스트 도구")
    print("1. 피드백 생성 및 알림 테스트")
    print("2. 기존 스트림 메시지 읽기")
    
    choice = input("\n선택하세요 (1 또는 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_feedback_notification())
    elif choice == "2":
        asyncio.run(read_stream_messages())
    else:
        print("❌ 잘못된 선택입니다")

if __name__ == "__main__":
    main()
