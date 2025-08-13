from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from fastapi.encoders import jsonable_encoder
from typing import List

from dependencies.auth_dependency import get_current_user

from dependencies.service_dependency import get_feedback_service
from model.response_models import SuccessResponse
from service.feedback.feedback_service import FeedbackService
from database.models import Feedback
from sqlalchemy.ext.asyncio import AsyncSession
from utils.db import get_db
from datetime import date


feedback_router = APIRouter(prefix="/api/ai/feedbacks", tags=["feedback"])
security_scheme = HTTPBearer()


@feedback_router.post("/create", response_model=SuccessResponse)
async def create_feedback(
    feedback_dto: FeedbackCreateDTO,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """피드백 생성"""
    try:
        feedback = Feedback(
            chat_id=feedback_dto.chat_id,
            feedback_type=feedback_dto.feedback_type,
            feedback_reason=feedback_dto.feedback_reason,
            feedback_content=feedback_dto.feedback_content,
            answer=feedback_dto.answer
        )
        
        created_feedback = await feedback_service.create_feedback(feedback)
        
        return SuccessResponse(
            success=True,
            result=jsonable_encoder(created_feedback),
            message="피드백이 성공적으로 생성되었습니다.",
            code=200
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 생성 중 오류가 발생했습니다: {str(e)}")
    
@feedback_router.get("/unlike_feedback_list", response_model=SuccessResponse)
async def get_unlike_feedback_list(
    current_user: dict = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """회사별 싫어요 피드백 목록 조회"""
    try:
         unlike_feedback_list = await feedback_service.get_company_unlike_feedback_list(current_user.get("company_id"))
         return SuccessResponse(
            success=True,   
            result=jsonable_encoder(unlike_feedback_list),
            message="싫어요 피드백 목록이 성공적으로 조회되었습니다.",
            code=200
         )
    except Exception as e:
       raise HTTPException(status_code=500, detail=f"싫어요 피드백 목록 조회 중 오류가 발생했습니다: {str(e)}")

@feedback_router.get("/monthly_count", response_model=SuccessResponse)
async def get_monthly_feedback_count(
    year: int,
    current_user: dict = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """회사별 월별 싫어요 피드백 수 조회"""
    try:
        monthly_feedback_count = await feedback_service.get_monthly_feedback_count(current_user.get("company_id"), year)
        return SuccessResponse(
            success=True,
            result=jsonable_encoder(monthly_feedback_count),
            message="월별 싫어요 피드백 수가 성공적으로 조회되었습니다.",
            code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"월별 피드백 수 조회 중 오류가 발생했습니다: {str(e)}")
    
@feedback_router.get("/daily_count", response_model=SuccessResponse)
async def get_daily_feedback_count(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """회사별 일별 싫어요 피드백 수 조회"""
    try:
        daily_feedback_count = await feedback_service.get_daily_feedback_count(current_user.get("company_id"), year, month)
        return SuccessResponse(
            success=True,
            result=jsonable_encoder(daily_feedback_count),
            message="일별 싫어요 피드백 수가 성공적으로 조회되었습니다.",
            code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일별 피드백 수 조회 중 오류가 발생했습니다: {str(e)}")
    
@feedback_router.get("/weekly_count", response_model=SuccessResponse)
async def get_weekly_feedback_count(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """회사별 주별 싫어요 피드백 수 조회"""
    try:
        weekly_feedback_count = await feedback_service.get_weekly_feedback_count(current_user.get("company_id"), year, month)
        return SuccessResponse(
            success=True,
            result=jsonable_encoder(weekly_feedback_count),
            message="주별 싫어요 피드백 수가 성공적으로 조회되었습니다.",
            code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주별 피드백 수 조회 중 오류가 발생했습니다: {str(e)}")


@feedback_router.get("/hourly_count", response_model=SuccessResponse)
async def get_hourly_feedback_count(
    date: str = Query(..., description="조회할 날짜 (YYYY-MM-DD 형식)"),
    company_id: int = Query(..., description="회사 ID"),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """특정 날짜의 시간별 피드백 수를 조회합니다."""
    try:
        # 날짜 형식 검증
        from datetime import datetime
        datetime.strptime(date, "%Y-%m-%d")
        
        result = await feedback_service.get_hourly_feedback_count(date, company_id)
        return SuccessResponse(
            success=True,
            result=jsonable_encoder(result),
            message="시간별 피드백 수가 성공적으로 조회되었습니다.",
            code=200
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시간별 피드백 수 조회 중 오류가 발생했습니다: {str(e)}")

@feedback_router.get("/ratio", response_model=SuccessResponse)
async def get_feedback_ratio(
    company_id: int = Query(..., description="회사 ID"),
    start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD 형식)"),
    end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD 형식)"),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """특정 날짜 구간의 LIKE/UNLIKE 피드백 비율을 조회합니다."""
    try:
        # 날짜 형식 검증
        from datetime import datetime
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
        
        result = await feedback_service.get_feedback_ratio(company_id, start_date, end_date)
        return SuccessResponse(
            success=True,
            result=jsonable_encoder(result),
            message="피드백 비율이 성공적으로 조회되었습니다.",
            code=200
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 비율 조회 중 오류가 발생했습니다: {str(e)}")

@feedback_router.get("/reasons", response_model=List[dict])
async def get_feedback_reasons():
    """피드백 사유 선택지 목록을 반환합니다."""
    feedback_reasons = [
        {"value": "OUTDATED_INFO", "label": "오래된 정보"},
        {"value": "INTENT_FAILURE", "label": "질문 의도 파악 실패"},
        {"value": "WRONG_ANSWER", "label": "잘못된 답변"},
        {"value": "MISSING_INFO", "label": "정보 누락"},
        {"value": "OTHER", "label": "기타"}
    ]
    return feedback_reasons

    
@feedback_router.delete("/delete/{feedback_id}", response_model=SuccessResponse)
async def delete_feedback(
    feedback_id: int,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """피드백 삭제"""
    try:
        await feedback_service.delete_feedback(feedback_id)
        return SuccessResponse(
            success=True,
            result=stats,
            message="피드백 사유 통계가 성공적으로 조회되었습니다.",
            code=200
        )
    except KeyError:
        raise HTTPException(status_code=401, detail="JWT 토큰에 company_id가 포함되어 있지 않습니다.")
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.")
    except Exception as e:
        # 기타 서버 오류
        raise HTTPException(status_code=500, detail=f"피드백 삭제 중 오류가 발생했습니다: {str(e)}")
    
@feedback_router.get("/top", response_model=List[TopKeywordDTO])
async def get_top_keywords(
    company_id: int,
    start_date: date = Query(..., description="조회 시작 날짜 (YYYY-MM-DD)"),
    end_date: date = Query(..., description="조회 종료 날짜 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """
    선택된 기간 내에 가장 많이 호출된 Top 10 키워드와 각 키워드의 호출 수를 반환합니다.
    """
    keyword_repo = KeywordRepository(db)
    keyword_service = KeywordService(keyword_repo)
    
    top_keywords = await keyword_service.get_top_keywords(
        company_id=company_id, start_date=start_date, end_date=end_date
    )
    return top_keywords

@feedback_router.get("/reason-stats", response_model=SuccessResponse)
async def get_feedback_reason_statistics(
    start_date: str = Query(None, description="시작 날짜 (YYYY-MM-DD)", regex=r'^\d{4}-\d{2}-\d{2}$'),
    end_date: str = Query(None, description="종료 날짜 (YYYY-MM-DD)", regex=r'^\d{4}-\d{2}-\d{2}$'),
    current_user: dict = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)):
        """회사별 피드백 사유 통계를 조회합니다."""    
        try: 
            company_id = current_user.get("company_id")                
            # 피드백 사유 통계 조회        
            stats = await feedback_service.get_feedback_reason_stats(company_id, start_date, end_date)                
            return SuccessResponse(            
                success=True,            
                result=stats,            
                message="피드백 사유 통계가 성공적으로 조회되었습니다.",            
                code=200        
                )    
        except KeyError:        
            raise HTTPException(status_code=401, detail="JWT 토큰에 company_id가 포함되어 있지 않습니다.")    
        except ValueError:        
            raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.")    
        except Exception as e:        
            raise HTTPException(status_code=500, detail=f"피드백 사유 통계 조회 중 오류가 발생했습니다: {str(e)}")