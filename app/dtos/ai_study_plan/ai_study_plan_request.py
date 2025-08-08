from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# Enumeration representing study plan status
class StudyPlanStatus(str, Enum):
    """학습 계획 진행 상황"""
    PLANNED = "planned"      # 계획 완료 (시작 전)
    ACTIVE = "active"        # 진행중
    COMPLETED = "completed"  # 완료됨
    PAUSED = "paused"        # 일시 정지
    CANCELLED = "cancelled"  # 취소됨


# =============================================================================
# 공부 계획 제작 요청 DTO
# =============================================================================

class AIStudyPlanCreateRequest(BaseModel):
    """AI 학습 계획 작성 요청 DTO"""
    
    user_id: int                                                # 학습 계획을 요청 하는 사용자 ID
    is_challenge: Annotated[bool, Field(default=False)]         # 챌린지 여부(True: 챌린지, False: 일반 공부 계획)
    input_data: str                                             # 학습 계획 제작 요청에 대한 사용자 입력 prompt
    start_date: datetime                                        # 공부 시작일
    end_date: datetime                                          # 공부 종료일


class AIStudyPlanUpdateRequest(BaseModel):
    """AI 학습 계획 업데이트 / 보완 요청 DTO"""
    
    input_data: Optional[str] = Field(default=None)            # 사용자 입력 prompt 수정
    output_data: Optional[str] = Field(default=None)           # AI가 생성한 학습 계획 수정
    start_date: Optional[datetime] = Field(default=None)       # 공부 시작일 수정
    end_date: Optional[datetime] = Field(default=None)         # 공부 종료일 수정
    is_challenge: Optional[bool] = Field(default=None)         # 챌린지 여부 수정
    status: Optional[StudyPlanStatus] = Field(default=None)    # 진행 상황 수정
