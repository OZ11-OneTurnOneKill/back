from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import logging

from app.dtos.ai_study_plan.study_plan import (
    StudyPlanRequest,
    StudyPlanResponse,
    StudyPlanUpdate,
    AsyncTaskResponse
)
from app.services.ai_services.study_plan_service import StudyPlanService
from app.services.ai_services.gemini_service import GeminiService
from app.configs.gemini_connect import gemini_api_key  # 설정에서 API 키 가져오기

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/study_plan",
    tags=["AI Study Plan"],
    responses={404: {"description": "Not found"}}
)


def get_study_plan_service() -> StudyPlanService:
    """StudyPlanService 의존성 주입"""
    api_key = gemini_api_key
    gemini_service = GeminiService(api_key=api_key)
    return StudyPlanService(gemini_service=gemini_service)


@router.post("/{user_id}", status_code=status.HTTP_201_CREATED, response_model=AsyncTaskResponse)
async def create_study_plan(
        user_id: int,
        request: StudyPlanRequest,
        study_plan_service: StudyPlanService = Depends(get_study_plan_service)
) -> AsyncTaskResponse:
    """AI 공부 학습 계획 생성 (프롬프트로) (비동기 진행 이유)

    Args:
        user_id: 사용자 ID
        request: 학습계획 생성 요청
        study_plan_service: 학습계획 서비스

    Returns:
        생성 결과 응답
    """
    try:
        logger.info(f"Creating study plan for user {user_id}")

        # 학습계획 생성
        study_plan = await study_plan_service.create_study_plan(
            user_id=user_id,
            request=request
        )

        return AsyncTaskResponse(
            success=True,
            message="AI가 성공적으로 공부 계획을 생성하였습니다.",
            data={
                "study_plans": study_plan.dict()
            },
            status="completed"
        )

    except ValueError as e:
        logger.warning(f"Validation error creating study plan for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=AsyncTaskResponse(
                success=False,
                message=str(e),
                status="failed"
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error creating study plan for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=AsyncTaskResponse(
                success=False,
                message=f"학습계획 생성 중 오류가 발생했습니다: {str(e)}",
                status="failed"
            ).dict()
        )


@router.get("/{user_id}", response_model=AsyncTaskResponse)
async def get_user_study_plans(
        user_id: int,
        limit: int = 10,
        offset: int = 0,
        study_plan_service: StudyPlanService = Depends(get_study_plan_service)
) -> AsyncTaskResponse:
    """AI 공부 학습 계획 데이터 출력

    Args:
        user_id: 사용자 ID
        limit: 조회 개수 제한
        offset: 건너뛸 개수
        study_plan_service: 학습계획 서비스

    Returns:
        사용자의 학습계획 목록
    """
    try:
        study_plans = await study_plan_service.get_user_study_plans(
            user_id=user_id,
            limit=limit,
            offset=offset
        )

        return AsyncTaskResponse(
            success=True,
            message="학습계획 목록을 성공적으로 조회했습니다.",
            data={
                "study_plans": [plan.dict() for plan in study_plans]
            }
        )

    except Exception as e:
        logger.error(f"Error fetching study plans for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AsyncTaskResponse(
                success=False,
                message=f"학습계획 조회 중 오류가 발생했습니다: {str(e)}"
            ).dict()
        )


@router.get("/{user_id}/{plan_id}", response_model=AsyncTaskResponse)
async def get_study_plan_by_id(
        user_id: int,
        plan_id: int,
        study_plan_service: StudyPlanService = Depends(get_study_plan_service)
) -> AsyncTaskResponse:
    """특정 학습계획 조회

    Args:
        user_id: 사용자 ID
        plan_id: 학습계획 ID
        study_plan_service: 학습계획 서비스

    Returns:
        학습계획 상세 정보
    """
    try:
        study_plan = await study_plan_service.get_study_plan_by_id(
            study_plan_id=plan_id,
            user_id=user_id
        )

        return AsyncTaskResponse(
            success=True,
            message="학습계획을 성공적으로 조회했습니다.",
            data={
                "study_plans": study_plan.dict()
            }
        )

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=AsyncTaskResponse(
                    success=False,
                    message=str(e)
                ).dict()
            )
        elif "access denied" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=AsyncTaskResponse(
                    success=False,
                    message=str(e)
                ).dict()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=AsyncTaskResponse(
                    success=False,
                    message=str(e)
                ).dict()
            )
    except Exception as e:
        logger.error(f"Error fetching study plan {plan_id} for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AsyncTaskResponse(
                success=False,
                message=f"학습계획 조회 중 오류가 발생했습니다: {str(e)}"
            ).dict()
        )


@router.post("/{user_id}/{plan_id}", response_model=AsyncTaskResponse)
async def update_study_plan(
        user_id: int,
        plan_id: int,
        update_data: Dict[str, Any],
        study_plan_service: StudyPlanService = Depends(get_study_plan_service)
) -> AsyncTaskResponse:
    """공부 학습 계획 업데이트 요청

    Args:
        user_id: 사용자 ID
        plan_id: 학습계획 ID
        update_data: 업데이트할 데이터
        study_plan_service: 학습계획 서비스

    Returns:
        업데이트된 학습계획
    """
    try:
        updated_plan = await study_plan_service.update_study_plan(
            study_plan_id=plan_id,
            user_id=user_id,
            update_data=update_data
        )

        return AsyncTaskResponse(
            success=True,
            message="학습계획이 성공적으로 업데이트되었습니다.",
            data={
                "study_plans": updated_plan.dict()
            }
        )

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=AsyncTaskResponse(
                    success=False,
                    message=str(e)
                ).dict()
            )
        elif "access denied" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=AsyncTaskResponse(
                    success=False,
                    message=str(e)
                ).dict()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=AsyncTaskResponse(
                    success=False,
                    message=str(e)
                ).dict()
            )
    except Exception as e:
        logger.error(f"Error updating study plan {plan_id} for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AsyncTaskResponse(
                success=False,
                message=f"학습계획 업데이트 중 오류가 발생했습니다: {str(e)}"
            ).dict()
        )


@router.delete("/{user_id}/{plan_id}", response_model=AsyncTaskResponse)
async def delete_study_plan(
        user_id: int,
        plan_id: int,
        study_plan_service: StudyPlanService = Depends(get_study_plan_service)
) -> AsyncTaskResponse:
    """공부 학습 계획 삭제

    Args:
        user_id: 사용자 ID
        plan_id: 학습계획 ID
        study_plan_service: 학습계획 서비스

    Returns:
        삭제 결과
    """
    try:
        await study_plan_service.delete_study_plan(
            study_plan_id=plan_id,
            user_id=user_id
        )

        return AsyncTaskResponse(
            success=True,
            message="학습 계획을 성공적으로 삭제했습니다."
        )

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=AsyncTaskResponse(
                    success=False,
                    message=str(e)
                ).dict()
            )
        elif "access denied" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=AsyncTaskResponse(
                    success=False,
                    message=str(e)
                ).dict()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=AsyncTaskResponse(
                    success=False,
                    message=str(e)
                ).dict()
            )
    except Exception as e:
        logger.error(f"Error deleting study plan {plan_id} for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AsyncTaskResponse(
                success=False,
                message=f"학습계획 삭제 중 오류가 발생했습니다: {str(e)}"
            ).dict()
        )