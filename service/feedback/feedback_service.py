import asyncio
from datetime import datetime
from database.repository.feedback_repository import FeedbackRepository
from database.repository.chunk_repository import ChunkRepository
from database.repository.chat_repository import ChatRepository
from database.models import Feedback, FeedbackType, FeedbackReason
from utils.db import async_redis_client
from typing import List, Optional
import httpx
import traceback
import json

from api.routes.feedback.feedbackDTO import UserInfoResponse
from config import settings


class FeedbackService:
    def __init__(self, feedback_repository: FeedbackRepository, chunk_repository: ChunkRepository, chat_repository: ChatRepository):
        self.feedback_repository = feedback_repository
        self.chunk_repository = chunk_repository
        self.chat_repository = chat_repository
        
    async def create_feedback(self, feedback: Feedback, authorization: str):
        """
        피드백 타입(좋아요, 싫어요)에 따른 처리를 수행합니다.
        """
        created_feedback = None
        
        try:
            # 피드백 타입에 따른 처리
            if feedback.feedback_type == FeedbackType.LIKE:
                created_feedback = await self.feedback_repository.create_feedback(feedback)
                # 피드백에 있는 chat_id의 모든 chunk_id를 추출
                chunk_ids = await self.chat_repository.get_chunk_ids_by_chat_id(feedback.chat_id)
                # 해당 chat_id에 있는 chunk_id들의 가중치를 1.1배 증가
                await self.chunk_repository.update_chunk_weights(chunk_ids)
        
            elif feedback.feedback_type == FeedbackType.UNLIKE:
                # 싫어요 피드백을 데이터베이스에 저장
                created_feedback = await self.feedback_repository.create_feedback(feedback)
            
            # 모든 비즈니스 로직이 성공적으로 완료된 후에만 알림 발행
            if created_feedback:
                try:
                    await self._publish_feedback_notification(created_feedback, authorization)
                except Exception as notification_error:
                    print(f"알림 발행 실패 (피드백 생성은 성공): {notification_error}")
                
            return created_feedback
            
        except Exception as e:
            # 핵심 비즈니스 로직 오류 발생 시 (DB 저장, chunk 가중치 업데이트 등)
            print(f"피드백 생성 중 오류 발생: {e}")
            raise  # 상위로 예외 전파하여 롤백 처리

    async def _publish_feedback_notification(self, feedback: Feedback, authorization: str):
        """피드백 생성 시 Redis Stream으로 알림을 발행합니다."""
        user_id = 0
        department = "Unknown"

        # --- 피드백 사유 한글 매핑 딕셔너리 ---
        feedback_reason_korean = {
            FeedbackReason.OUTDATED_INFO: "오래된 정보",
            FeedbackReason.INTENT_FAILURE: "질문 의도 파악 실패",
            FeedbackReason.WRONG_ANSWER: "잘못된 답변",
            FeedbackReason.MISSING_INFO: "정보 누락",
            FeedbackReason.OTHER: "기타"
        }
        # --- 피드백 사유 한글 매핑 딕셔너리 ---

        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": authorization}

                # 실제 요청
                response = await client.get(
                    f"{settings.USER_API_URL}/api/users/info/me",
                    headers=headers
                )

                # 상태 코드 검사
                response.raise_for_status()

                # JSON 파싱 전 데이터 구조 확인
                try:
                    response_json = response.json()
                except Exception as json_err:
                    traceback.print_exc()
                    return

                # Pydantic 모델 검증
                try:
                    user_info = UserInfoResponse.model_validate(response_json)
                except Exception as model_err:
                    traceback.print_exc()
                    return

                # 필요한 값 추출
                user_id = user_info.result.userId
                department = user_info.result.departmentName
                company_id = user_info.result.companyId
                print(f"✅ [API] 사용자 ID({user_id}), 회사ID({company_id}), 부서({department}) 조회 성공")

        except httpx.HTTPStatusError as http_err:
            print(f"[ERROR] HTTP 상태 코드 오류: {http_err}")
            traceback.print_exc()
        except httpx.RequestError as req_err:
            print(f"[ERROR] 요청 자체 실패 (네트워크 문제 등): {req_err}")
            traceback.print_exc()
        except Exception as e:
            print(f"🚨 [API] 사용자 정보 조회 중 알 수 없는 오류 발생: {e}")
            traceback.print_exc()

        notification_description = ""
        if feedback.feedback_type == FeedbackType.UNLIKE:
            if feedback.feedback_reason == FeedbackReason.OTHER:
                # '기타' 사유일 경우, 사용자가 입력한 content를 description으로 사용
                notification_description = feedback.feedback_content or "기타 의견 (내용 없음)"
            elif feedback.feedback_reason in feedback_reason_korean:
                # '기타'가 아닌 다른 명시적 사유가 있을 경우, 한글 맵에서 해당 사유를 찾아 description으로 사용
                notification_description = feedback_reason_korean[feedback.feedback_reason]
            else:
                # UNLIKE 이지만 사유가 없는 경우에 대한 예외 처리
                notification_description = "분류되지 않은 싫어요 피드백"
        
        print(f"✅ [DEBUG] Redis 전송 예정 데이터 | senderId: {user_id}, department: '{department}', description: '{notification_description}'")
            
        try:
            # Redis Stream에 알림 전송
            await async_redis_client.xadd(
                "notification-stream",
                {
                    "senderId": str(user_id),
                    "type": "FEEDBACK",
                    "companyId": str(company_id),
                    "department": str(department),
                    "description": notification_description,
                    "createdAt": datetime.utcnow().isoformat()
                }
            )
            print(f"[Redis Stream] 피드백 알림 발행 완료: feedback_id={feedback.feedback_id}")
            
        except Exception as e:
            print(f"[Redis Stream] 알림 발행 중 오류 발생: {e}")
            # 알림 발행 실패해도 피드백 생성은 성공으로 처리
    
    async def get_company_unlike_feedback_list(self, company_id: int):
        """회사별 unlike 피드백 목록 조회"""
        return await self.feedback_repository.get_company_unlike_feedback_list(company_id)
    
    async def get_company_feedback_list(self, company_id: int):
        """회사별 모든 피드백 목록 조회"""
        return await self.feedback_repository.get_company_feedback_list(company_id)
    
    async def get_monthly_feedback_count(self, company_id: int, year: int):
        """회사별 월별 피드백 수 조회"""
        return await self.feedback_repository.get_monthly_feedback_count(company_id, year)
    
    async def get_daily_feedback_count(self, company_id: int, year: int, month: int):
        """회사별 일별 피드백 수 조회"""
        return await self.feedback_repository.get_daily_feedback_count(company_id, year, month)
    
    async def get_weekly_feedback_count(self, company_id: int, year: int, month: int):
        """회사별 주별 피드백 수 조회"""
        return await self.feedback_repository.get_weekly_feedback_count(company_id, year, month)
    
    async def get_hourly_feedback_count(self, date: str, company_id: int) -> List[dict]:
        """특정 날짜의 시간별 피드백 수를 조회합니다."""
        return await self.feedback_repository.get_hourly_feedback_count(date, company_id)

    async def get_feedback_ratio(self, company_id: int, start_date: str, end_date: str) -> dict:
        """특정 날짜 구간의 LIKE/UNLIKE 피드백 비율을 조회합니다."""
        return await self.feedback_repository.get_feedback_ratio(company_id, start_date, end_date)
    
    async def delete_feedback(self, feedback_id: int):
        """피드백 삭제"""
        deleted = await self.feedback_repository.delete_feedback(feedback_id)
        
        if not deleted:
            raise ValueError(f"피드백 ID {feedback_id}를 찾을 수 없습니다.")
        
        return deleted
    
    async def get_feedback_reason_stats(self, company_id: int, start_date: str = None, end_date: str = None):
        """회사별 피드백 사유 통계 조회"""
        return await self.feedback_repository.get_feedback_reason_stats(company_id, start_date, end_date)