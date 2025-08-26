from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChallengeProgressResponse(BaseModel):
    """챌린지 진행상황 응답 스키마"""

    id: int = Field(..., description="챌린지 진행상황 ID")
    study_plan_id: int = Field(..., description="학습계획 ID")
    user_id: int = Field(..., description="사용자 ID")
    status: Optional[str] = Field(None, description="챌린지 진행 상태 (진행 중, 진행 완료, 실패)")
    challenge_image_url: Optional[str] = Field(None, description="챌린지 관련 이미지 URL")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")


class ChallengeProgressUpdate(BaseModel):
    """챌린지 진행상황 업데이트 스키마"""

    status: Optional[str] = Field(None, description="챌린지 진행 상태")
    challenge_image_url: Optional[str] = Field(None, description="챌린지 관련 이미지 URL")


# 기존 study_plan.py에 추가할 내용
class StudyPlanWithChallengeResponse(BaseModel):
    """학습계획과 챌린지 정보가 포함된 응답 스키마"""

    id: int = Field(..., description="학습계획 ID")
    user_id: int = Field(..., description="사용자 ID")
    input_data: str = Field(..., description="사용자 입력 데이터")
    output_data: Optional[str] = Field(None, description="AI 생성 학습계획")
    is_challenge: bool = Field(default=False, description="챌린지 여부")
    start_date: datetime = Field(..., description="학습 시작일")
    end_date: datetime = Field(..., description="학습 종료일")
    created_at: datetime = Field(..., description="생성일시")

    # 챌린지 정보 (is_challenge=True일 때만 존재)
    challenge_progress: Optional[ChallengeProgressResponse] = Field(None, description="챌린지 진행상황")