from typing import Optional, Literal
from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo
from datetime import datetime


# ===== (테스트용) 공통 게시글 요청 DTO =====
# class CommonPostRequest(BaseModel):
#     title: str
#     content: str
#     category: str

# ===== 스터디 모집 요청 DTO =====
class StudyPostRequest(BaseModel):
    title: str
    content: str
    category: Literal["study"] = "study"
    user_id: int
    recruit_start: datetime
    recruit_end: datetime
    study_start: datetime
    study_end: datetime
    max_member: int

    @field_validator("study_end")
    def validate_study_period(cls, v, info: ValidationInfo):
        start_date = info.data.get("study_start")
        if start_date and v < start_date:
            raise ValueError("스터디 종료일은 시작일 이후여야 합니다")
        return v

    @field_validator("recruit_end")
    def validate_recruit_period(cls, v, info: ValidationInfo):
        start_date = info.data.get("recruit_start")
        if start_date and v < start_date:
            raise ValueError("구인 마감일은 시작일 이후여야 합니다")
        return v


# ===== 자유게시판 요청 DTO =====
class FreePostRequest(BaseModel):
    title: str
    content: str
    category: Literal["free"] = "free"
    user_id: int
    image_url: str | None = None


# ===== 자료공유 요청 DTO =====
class SharePostRequest(BaseModel):
    title: str
    content: str
    category: Literal["share"] = "share"
    user_id: int
    file_url: str | None = None


class StudyPostUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    study_start: Optional[datetime] = None
    study_end: Optional[datetime] = None
    recruit_start: Optional[datetime] = None
    recruit_end: Optional[datetime] = None
    max_member: Optional[int] = None


class CommentRequest(BaseModel):
    post_id: int
    content: str
    parent_id: Optional[int] = None
    user_id: int


class StudyJoinRequest(BaseModel):
    user_id: int


class LikeToggleRequest(BaseModel):
    user_id: int