from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from fastapi.encoders import jsonable_encoder

from api.routes.feedback.feedbackDTO import FeedbackCreateDTO
from dependencies.service_dependency import get_feedback_service
from model.response_models import SuccessResponse
from service.feedback.feedback_service import FeedbackService
from database.models import Feedback

feedback_router = APIRouter(prefix="/api/ai/feedbacks", tags=["feedback"])
security_scheme = HTTPBearer()


@feedback_router.post("/create", response_model=SuccessResponse)
async def create_feedback(
    feedback_dto: FeedbackCreateDTO,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    try:
        feedback = Feedback(
            chat_id=feedback_dto.chat_id,
            feedback_type=feedback_dto.feedback_type,
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
    company_id: int,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    try:
         unlike_feedback_list = await feedback_service.get_company_unlike_feedback_list(company_id)
         return SuccessResponse(
            success=True,   
            result=jsonable_encoder(unlike_feedback_list),
             message="싫어요 피드백 목록이 성공적으로 조회되었습니다.",
             code=200
         )
    except Exception as e:
       raise HTTPException(status_code=500, detail=f"싫어요 피드백 목록 조회 중 오류가 발생했습니다: {str(e)}")