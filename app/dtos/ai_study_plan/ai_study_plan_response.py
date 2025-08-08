from datetime import datetime
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# 학습 계획 상태를 나타내는 Enumeration
class StudyPlanStatus(str, Enum):
    """공부 계획 진행 상황"""
    PLANNED = "planned"      # 계획 완료 (시작 전)
    ACTIVE = "active"        # 진행중
    COMPLETED = "completed"  # 완료됨
    PAUSED = "paused"        # 일시 정지
    CANCELLED = "cancelled"  # 취소됨


# =============================================================================
# 공부 계획 제작 응답 DTO
# =============================================================================

class AIStudyPlanResponse(BaseModel):
    """AI 공부 계획 응답 DTO(전체 정보)"""

    id: int                         # 학습 계획 ID
    user_id: int                    # 학습 계획 소유자 ID
    is_challenge: bool              # 챌린지 여부
    input_data: str                 # 학습 계획 생성 요청에 대한 사용자 입력 prompt
    output_data: str                # AI가 생성한 학습 계획
    start_date: datetime            # 학습 시작일
    end_date: datetime              # 학습 종료일

    # Additional information fields
    status: StudyPlanStatus = Field(default=StudyPlanStatus.PLANNED, description="현재 공부 계획 진행 상황")

    # Metadata
    created_at: datetime            # 생성된 시간
    updated_at: datetime            # 마지막으로 수정된 시간

    # Computed fields
    is_active: Annotated[bool, Field(default=False)]            # 현재 활성화 여부
    progress_percentage: Optional[int] = Field(default=None, ge=0, le=100)    # 진행률 (0-100%)
    days_remaining: Optional[int] = Field(default=None)         # 남은 일수(기한이 지난 경우 음수)