from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field

PostCategory = Literal["study", "free", "share"]
BadgeType    = Literal["모집중", "모집완료"]

class PostSummary(BaseModel):
    id: int
    category: PostCategory
    title: str
    author_id: int
    author_nickname: Optional[str] = None
    views: int
    created_at: datetime

    # study 전용(모집 기간 내에서만 세팅)
    badge: Optional[BadgeType] = Field(
        None, description="study 전용 배지 (모집 기간 내에서만 표시)"
    )
    remaining: Optional[int] = Field(
        None, ge=0, description="남은 정원 (badge가 있을 때만 세팅)"
    )
    max_member: Optional[int] = Field(
        None, description="모집 정원 (badge가 있을 때만 세팅)"
    )

class CursorListResponse(BaseModel):
    count: int
    next_cursor: Optional[int] = Field(
        None, description="다음 페이지 요청에 사용할 커서(id). 없으면 마지막 페이지"
    )
    items: List[PostSummary]
