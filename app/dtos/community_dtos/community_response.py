from typing import Optional, List, Literal, Annotated, Union
from pydantic import BaseModel, Field
from datetime import datetime
# === 공통 ===
StudyLiteral = Literal["study"]
FreeLiteral  = Literal["free"]
ShareLiteral = Literal["share"]

# ----- 첨부 스키마 -----
class FreeImageOut(BaseModel):
    id: int
    image_url: str
    mime_type: str
    size_bytes: int
    created_at: datetime

class ShareFileOut(BaseModel):
    id: int
    file_url: str
    mime_type: str
    size_bytes: int
    created_at: datetime

# ----- 스터디 상세 -----
class StudyRecruitmentResponse(BaseModel):
    recruit_start: datetime
    recruit_end: datetime
    study_start: datetime
    study_end: datetime
    max_member: int

class StudyPostResponse(BaseModel):
    id: int
    title: str
    content: str
    category: StudyLiteral
    author_id: int
    author_nickname: Optional[str] = None
    views: int
    like_count: int
    comment_count: int
    study_recruitment: StudyRecruitmentResponse
    created_at: datetime
    updated_at: datetime

# ----- 자유게시판 상세 -----
class FreePostResponse(BaseModel):
    id: int
    title: str
    content: str
    category: FreeLiteral
    author_id: int
    author_nickname: Optional[str] = None
    views: int
    like_count: int
    comment_count: int
    images: List[FreeImageOut] = []
    created_at: datetime
    updated_at: datetime

# ----- 자료공유 상세 -----
class SharePostResponse(BaseModel):
    id: int
    title: str
    content: str
    category: ShareLiteral
    author_id: int
    author_nickname: Optional[str] = None
    views: int
    like_count: int
    comment_count: int
    files: List[ShareFileOut] = []
    created_at: datetime
    updated_at: datetime

class CommentResponse(BaseModel):
    id: int
    post_id: int
    content: str
    author_id: int
    author_nickname: Optional[str] = None
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class CommentListResponse(BaseModel):
    total: int
    count: int
    items: list[CommentResponse]

PostDetailResponse = Annotated[
    Union[StudyPostResponse, FreePostResponse, SharePostResponse],
    Field(discriminator="category")
]