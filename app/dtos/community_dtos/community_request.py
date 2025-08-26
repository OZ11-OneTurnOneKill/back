from typing import Optional, Literal, Annotated, Union
from pydantic import BaseModel, field_validator, Field, ConfigDict, AliasChoices, constr, AliasPath
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

    recruit_start: datetime = Field(
        validation_alias=AliasChoices(
            "recruit_start",
            AliasPath("study", "recruit_start"),
            AliasPath("study_recruitment", "recruit_start"),
        )
    )
    recruit_end: datetime = Field(
        validation_alias=AliasChoices(
            "recruit_end",
            AliasPath("study", "recruit_end"),
            AliasPath("study_recruitment", "recruit_end"),
        )
    )
    study_start: datetime = Field(
        validation_alias=AliasChoices(
            "study_start",
            AliasPath("study", "study_start"),
            AliasPath("study_recruitment", "study_start"),
        )
    )
    study_end: datetime = Field(
        validation_alias=AliasChoices(
            "study_end",
            AliasPath("study", "study_end"),
            AliasPath("study_recruitment", "study_end"),
        )
    )
    max_member: int = Field(
        ge=1, le=MAX_STUDY_MEMBERS,
        validation_alias=AliasChoices(
            "max_member",
            AliasPath("study", "max_member"),
            AliasPath("study_recruitment", "max_member"),
        )
    )

    @field_validator("study_end")
    def validate_study_period(cls, v, info):
        start_date = info.data.get("study_start")
        if start_date and v < start_date:
            raise ValueError("스터디 종료일은 시작일 이후여야 합니다")
        return v

    @field_validator("recruit_end")
    def validate_recruit_period(cls, v, info):
        start_date = info.data.get("recruit_start")
        if start_date and v < start_date:
            raise ValueError("구인 마감일은 시작일 이후여야 합니다")
        return v


# ===== 자유게시판 요청 DTO =====
class FreePostCreate(BasePostCreate):
    category: Literal["free"] = "free"


# ===== 자료공유 요청 DTO =====
class SharePostCreate(BasePostCreate):
    category: Literal["share"] = "share"

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


# class ApplicationCreateRequest(BaseModel):
#     model_config = ConfigDict(extra='forbid')
#     message: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

