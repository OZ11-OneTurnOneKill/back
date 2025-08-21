from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

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
    category: str
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
    category: str
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
    category: str
    author_id: int
    author_nickname: Optional[str] = None
    views: int
    like_count: int
    comment_count: int
    files: List[ShareFileOut] = []
    created_at: datetime
    updated_at: datetime

# ----- 공통: 커서 기반 목록 -----
class CursorListItem(BaseModel):
    id: int
    category: str
    title: str
    author_id: int
    author_nickname: Optional[str] = None
    views: int
    created_at: datetime

class CursorListResponse(BaseModel):
    count: int
    next_cursor: Optional[int]
    items: List[CursorListItem]
