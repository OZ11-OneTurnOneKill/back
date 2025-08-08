from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from app.dtos.ai_study_plan.ai_study_plan_request import AIStudyPlanCreateRequest, AIStudyPlanUpdateRequest
from app.dtos.ai_study_plan.ai_study_plan_response import AIStudyPlanResponse
from app.services.ai_study_plan_service import AIStudyPlanService
from app.utils.exceptions import (
    StudyPlanNotFoundError,
    UserNotFoundError,
    ValidationError,
    DatabaseError,
    DuplicateStudyPlanError,
    InvalidDateRangeError,
    InsufficientPermissionsError
)

router = APIRouter(
    prefix="/api/v1/ai", 
    tags=["AI Study Plan"],
    responses={
        400: {"description": "Bad Request - Invalid input data"},
        404: {"description": "Not Found - Resource not found"},
        422: {"description": "Validation Error - Request validation failed"},
        500: {"description": "Internal Server Error"}
    }
)


@router.post(
    "/study-plans",
    response_model=AIStudyPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create AI Study Plan",
    description="Create a new AI-generated study plan with automatic status calculation",
    response_description="Successfully created study plan"
)
async def create_study_plan(request: AIStudyPlanCreateRequest) -> AIStudyPlanResponse:
    """새로운 AI 스터디 플랜 생성
    
    - **user_id**: 스터디 플랜을 생성할 사용자 ID
    - **is_challenge**: 챌린지 모드 여부 (선택사항, 기본값: False)
    - **input_data**: 사용자가 입력한 학습 목표 또는 요구사항
    - **start_date**: 학습 시작 예정일
    - **end_date**: 학습 종료 예정일 (시작일보다 나중이어야 함)
    """
    return await _handle_service_call(
        AIStudyPlanService.create_study_plan, request
    )


@router.get(
    "/study-plans",
    response_model=List[AIStudyPlanResponse],
    summary="Get Study Plans",
    description="Retrieve study plans with optional filtering and pagination",
    response_description="List of study plans matching the criteria"
)
async def get_study_plans(
    user_id: Optional[int] = Query(None, description="Filter by user ID", gt=0),
    is_challenge: Optional[bool] = Query(None, description="Filter by challenge mode"),
    status: Optional[str] = Query(None, description="Filter by status (planned, active, completed, paused, cancelled)"),
    limit: int = Query(20, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Number of results to skip", ge=0)
) -> List[AIStudyPlanResponse]:
    """스터디 플랜 목록 조회
    
    다양한 필터 조건과 페이징을 지원합니다:
    - 사용자별 필터링
    - 챌린지/일반 모드별 필터링
    - 상태별 필터링
    - 페이징 지원 (limit, offset)
    """
    return await _handle_service_call(
        AIStudyPlanService.get_study_plans,
        user_id=user_id,
        is_challenge=is_challenge,
        status=status,
        limit=limit,
        offset=offset
    )


@router.get(
    "/study-plans/{plan_id}",
    response_model=AIStudyPlanResponse,
    summary="Get Study Plan by ID",
    description="Retrieve a specific study plan with calculated progress and status",
    response_description="Study plan details with current progress information"
)
async def get_study_plan(plan_id: int) -> AIStudyPlanResponse:
    """특정 스터디 플랜 조회
    
    스터디 플랜 ID를 통해 상세 정보를 조회하며,
    현재 진행률과 상태가 자동으로 계산됩니다.
    """
    return await _handle_service_call(
        AIStudyPlanService.get_study_plan_by_id, plan_id
    )


@router.put(
    "/study-plans/{plan_id}",
    response_model=AIStudyPlanResponse,
    summary="Update Study Plan",
    description="Update an existing study plan with partial or complete data",
    response_description="Updated study plan with recalculated progress"
)
async def update_study_plan(
    plan_id: int, 
    request: AIStudyPlanUpdateRequest
) -> AIStudyPlanResponse:
    """스터디 플랜 업데이트
    
    기존 스터디 플랜의 일부 또는 전체 필드를 업데이트합니다.
    - 날짜 변경 시 자동으로 유효성 검증이 수행됩니다
    - 진행률과 상태가 자동으로 재계산됩니다
    """
    return await _handle_service_call(
        AIStudyPlanService.update_study_plan, plan_id, request
    )


@router.delete(
    "/study-plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Study Plan",
    description="Permanently delete a study plan"
)
async def delete_study_plan(plan_id: int) -> None:
    """스터디 플랜 삭제
    
    지정된 스터디 플랜을 영구적으로 삭제합니다.
    삭제 후에는 복구할 수 없으므로 주의하세요.
    """
    await _handle_service_call(
        AIStudyPlanService.delete_study_plan, plan_id
    )


@router.get(
    "/study-plans/user/{user_id}",
    response_model=List[AIStudyPlanResponse],
    summary="Get User Study Plans",
    description="Retrieve all study plans for a specific user with filtering options",
    response_description="List of study plans belonging to the user"
)
async def get_user_study_plans(
    user_id: int,
    is_challenge: Optional[bool] = Query(None, description="Filter by challenge mode"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Number of results to skip", ge=0)
) -> List[AIStudyPlanResponse]:
    """특정 사용자의 스터디 플랜 조회
    
    지정된 사용자의 모든 스터디 플랜을 조회하며,
    필터링과 페이징을 지원합니다.
    """
    return await _handle_service_call(
        AIStudyPlanService.get_user_study_plans,
        user_id=user_id,
        is_challenge=is_challenge,
        status=status,
        limit=limit,
        offset=offset
    )


@router.patch(
    "/study-plans/{plan_id}/status",
    response_model=AIStudyPlanResponse,
    summary="Update Study Plan Status",
    description="Update the status of a study plan manually",
    response_description="Study plan with updated status"
)
async def update_study_plan_status(
    plan_id: int,
    new_status: str = Query(..., description="New status (planned, active, completed, paused, cancelled)")
) -> AIStudyPlanResponse:
    """스터디 플랜 상태 업데이트
    
    스터디 플랜의 상태를 수동으로 변경합니다.
    유효한 상태값: planned, active, completed, paused, cancelled
    """
    return await _handle_service_call(
        AIStudyPlanService.update_study_plan_status, plan_id, new_status
    )


# 공통 예외 처리 헬퍼 함수
async def _handle_service_call(service_method, *args, **kwargs):
    """서비스 메서드 호출과 예외 처리를 통합적으로 처리하는 헬퍼 함수"""
    try:
        return await service_method(*args, **kwargs)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except StudyPlanNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except InvalidDateRangeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except DuplicateStudyPlanError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")