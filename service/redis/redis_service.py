# app/redis_service.py
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

from config import settings


class RedisService:
    def __init__(self, redis_client: redis.Redis):
        # 비동기 레디스 클라이언트를 주입받음
        self.redis_client = redis_client

    def _get_comparison_key(self, main_doc_id: int, compare_doc_id: int) -> str:
        return f"pdf_comparison:{main_doc_id}:{compare_doc_id}"

    def get_comparison(self, main_doc_id: int, compare_doc_id: int) -> Dict[str, Any] | None:
        try:
            key = self._get_comparison_key(main_doc_id, compare_doc_id)
            result = self.redis_client.get(key)
            return json.loads(result) if result else None
        except Exception as e:
            print(f"Redis 조회 중 오류 발생: {e}")
            return None

    def save_comparison(self, main_doc_id: int, compare_doc_id: int, main_text: str, compare_text: str, diff_result: str) -> bool:
        try:
            key = self._get_comparison_key(main_doc_id, compare_doc_id)
            redis_data = {
                "main_doc_id": main_doc_id,
                "compare_doc_id": compare_doc_id,
                "diff_result": diff_result,
                "timestamp": datetime.now().isoformat(),
            }
            self.redis_client.setex(
                key,
                172800,  # 48시간을 초 단위로 변환 (48 * 60 * 60)
                json.dumps(redis_data, ensure_ascii=False)
            )
            return True
        except Exception as e:
            print(f"Redis 저장 중 오류 발생: {e}")
            return False