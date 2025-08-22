from typing import Optional, Literal, Annotated, Union
from pydantic import BaseModel, field_validator, Field, ConfigDict, AliasChoices, constr
from pydantic_core.core_schema import ValidationInfo
from datetime import datetime
from app.core.constants import MAX_STUDY_MEMBERS


# ===== (테스트용) 공통 게시글 요청 DTO =====
# class CommonPostRequest(BaseModel):
#     title: str
#     content: str
#     category: str

class BasePostCreate(BaseModel):
    title: str
    content: str

# ===== 스터디 모집 요청 DTO =====
class StudyPostCreate(BasePostCreate):
    category: Literal["study"] = "study"
    user_id: int
    recruit_start: datetime
    recruit_end: datetime
    study_start: datetime
    study_end: datetime
    max_member: int = Field(ge=1,le=MAX_STUDY_MEMBERS)

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
class FreePostCreate(BasePostCreate):
    category: Literal["free"] = "free"
    user_id: int


# ===== 자료공유 요청 DTO =====
class SharePostCreate(BasePostCreate):
    category: Literal["share"] = "share"
    user_id: int

# 하나로 받기 위한 Discriminated Union (category 기준)
PostCreateRequest = Annotated[
    Union[StudyPostCreate, FreePostCreate, SharePostCreate],
    Field(discriminator="category"),
]

class PostUpdateAny(BaseModel):
    """
    카테고리 공통 PATCH 바디 (전부 선택적).
    study 전용 필드가 넘어와도 실제로 study가 아닌 글이면 서비스에서 무시됩니다.
    """
    model_config = ConfigDict(extra="forbid")

    # 공통
    title: Optional[str] = None
    content: Optional[str] = None

    # study 전용
    recruit_start: Optional[datetime] = None
    recruit_end: Optional[datetime] = None
    study_start: Optional[datetime] = None
    study_end: Optional[datetime] = None
    max_member: Optional[int] = Field(default=None, ge=1, le=MAX_STUDY_MEMBERS)
    
# class StudyPostUpdateRequest(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     title: Optional[str] = None
#     content: Optional[str] = None
#     study_start: Optional[datetime] = None
#     study_end: Optional[datetime] = None
#     recruit_start: Optional[datetime] = None
#     recruit_end: Optional[datetime] = None
#     max_member: Optional[int] | None = Field(None, ge=1, le=MAX_STUDY_MEMBERS)
#
# class FreePostUpdateRequest(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     title: Optional[str] = None
#     content: Optional[str] = None
#
#
#
# class SharePostUpdateRequest(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     title: Optional[str] = None
#     content: Optional[str] = None



class CommentRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: constr(max_length=50)
    parent_comment_id: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("parent_comment_id", "parent_id")
    )


class CommentUpdateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: constr(max_length=50)


class ApplicationCreateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

