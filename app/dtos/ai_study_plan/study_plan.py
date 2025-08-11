from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class StudyPlanRequest(BaseModel):
    """학습계획 생성 요청 스키마"""

    input_data: str = Field(..., min_length=1, description="사용자 입력 프롬프트")
    start_date: datetime = Field(..., description="학습 시작일")
    end_date: datetime = Field(..., description="학습 종료일")
    is_challenge: bool = Field(default=False, description="챌린지 여부")

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: datetime, info) -> datetime:
        """종료일이 시작일보다 늦은지 검증"""
        if info.data.get('start_date') and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class StudyPlanResponse(BaseModel):
    """학습계획 응답 스키마"""

    id: int = Field(..., description="학습계획 ID")
    user_id: int = Field(..., description="사용자 ID")
    input_data: str = Field(..., description="사용자 입력 데이터")
    output_data: Optional[str] = Field(None, description="AI 생성 학습계획")
    is_challenge: bool = Field(default=False, description="챌린지 여부")
    start_date: datetime = Field(..., description="학습 시작일")
    end_date: datetime = Field(..., description="학습 종료일")
    created_at: datetime = Field(..., description="생성일시")


class StudyPlanUpdate(BaseModel):
    """학습계획 업데이트 스키마"""

    input_data: Optional[str] = Field(None, min_length=1, description="수정된 입력 프롬프트")
    start_date: Optional[datetime] = Field(None, description="수정된 시작일")
    end_date: Optional[datetime] = Field(None, description="수정된 종료일")
    is_challenge: Optional[bool] = Field(None, description="챌린지 여부")

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: datetime, info) -> datetime:
        """종료일이 시작일보다 늦은지 검증"""
        if v and info.data.get('start_date') and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class AsyncTaskResponse(BaseModel):
    """비동기 작업 응답 스키마"""

    success: bool = Field(..., description="작업 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[dict] = Field(None, description="응답 데이터")
    status: str = Field(default="processing", description="작업 상태")