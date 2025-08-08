from typing import Optional

from pydantic import BaseModel
from datetime import datetime


# ===== (테스트용) 공통 게시글 응답 DTO =====
# class CommonPostResponse(BaseModel):
#     title: str
#     content: str
#     category: str


# ===== 스터디 모집 응답 DTO =====
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
    category: str
    author_id: int
    views: int
    study_recruitment: StudyRecruitmentResponse
    created_at: datetime
    updated_at: datetime


# ===== 자유게시판 응답 DTO =====
class FreeBoardResponse(BaseModel):
    image_url: Optional[str] = None


class FreePostResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    author_id: int
    views: int
    free_board: FreeBoardResponse
    created_at: datetime
    updated_at: datetime


# ===== 자료공유 응답 DTO =====
class DataShareResponse(BaseModel):
    file_url: str


class SharePostResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    author_id: int
    views: int
    data_share: DataShareResponse
    created_at: datetime
    updated_at: datetime


class CommentResponse(BaseModel):
    id: int
    post_id: int
    content: str
    author_id: int
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime