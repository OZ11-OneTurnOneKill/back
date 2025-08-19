from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
from app.exceptions.study_plan_exception import StudyPlanNotFoundError, StudyPlanAccessDeniedError
from app.dtos.ai.summary import SummaryRequest, SummaryResponse
from app.dtos.ai.study_plan import AsyncTaskResponse
from app.services.ai_services.summary_service import SummaryService
from app.services.ai_services.gemini_service import GeminiService
from app.services.users.users import get_current_user
from app.configs.gemini_connect import gemini_api_key

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/ai/summary",
    tags=["AI Summary"],
    responses={404: {"description": "Not found"}}
)

def get_summary_service() -> SummaryService:
    """SummaryService 의존성 주입"""
    api_key = gemini_api_key
    gemini_service = GeminiService(api_key=api_key)
    return SummaryService(gemini_service=gemini_service)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AsyncTaskResponse)
async def create_summary(
        request: SummaryRequest,
        summary_service: SummaryService = Depends(get_summary_service),
        current_user = Depends(get_current_user)
) -> AsyncTaskResponse:
    """AI 자료 요약 생성"""
    try:
        user_id = current_user.id
        logger.info(f"Creating summary for user {user_id}")

        summary = await summary_service.create_summary(
            user_id=user_id,
            request=request
        )

        return AsyncTaskResponse(
            success=True,
            message="AI가 성공적으로 자료를 요약했습니다.",
            data={"summary": summary.dict()},
            status="completed"
        )

    except Exception as e:
        logger.error(f"Error creating summary for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=AsyncTaskResponse(
                success=False,
                message=f"자료 요약 중 오류가 발생했습니다: {str(e)}",
                status="failed"
            ).dict()
        )

@router.get("/", response_model=AsyncTaskResponse)
async def get_user_summaries(
        limit: int = 10,
        offset: int = 0,
        summary_service: SummaryService = Depends(get_summary_service),
        current_user = Depends(get_current_user)
) -> AsyncTaskResponse:
    """사용자별 요약 목록 조회"""
    try:
        user_id = current_user.id
        summaries = await summary_service.get_user_summaries(
            user_id=user_id,
            limit=limit,
            offset=offset
        )

        return AsyncTaskResponse(
            success=True,
            message="요약 목록을 성공적으로 조회했습니다.",
            data={"summaries": [summary.dict() for summary in summaries]}
        )

    except Exception as e:
        logger.error(f"Error fetching summaries for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AsyncTaskResponse(
                success=False,
                message=f"요약 목록 조회 중 오류가 발생했습니다: {str(e)}"
            ).dict()
        )

@router.delete("/{summary_id}", response_model=AsyncTaskResponse)
async def delete_summary(
        summary_id: int,
        summary_service: SummaryService = Depends(get_summary_service),
        current_user = Depends(get_current_user)
) -> AsyncTaskResponse:
    """자료 요약 삭제

    Args:
        summary_id: 요약 ID
        summary_service: 요약 서비스
        current_user: 현재 사용자 (JWT에서 추출)

    Returns:
        삭제 결과
    """
    try:
        user_id = current_user.id
        logger.info(f"Attempting to delete summary {summary_id} for user {user_id}")

        await summary_service.delete_summary(
            summary_id=summary_id,
            user_id=user_id
        )

        return AsyncTaskResponse(
            success=True,
            message="요약을 성공적으로 삭제했습니다.",
            data={"deleted_summary_id": summary_id}
        )

    except StudyPlanNotFoundError as e:
        logger.warning(f"Summary not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=AsyncTaskResponse(
                success=False,
                message=str(e),
                data=e.details
            ).dict()
        )
    except StudyPlanAccessDeniedError as e:
        logger.warning(f"Access denied: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=AsyncTaskResponse(
                success=False,
                message=str(e),
                data=e.details
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error deleting summary {summary_id} for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AsyncTaskResponse(
                success=False,
                message="요약 삭제 중 오류가 발생했습니다."
            ).dict()
        )