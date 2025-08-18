from typing import Optional, Literal
from datetime import datetime
from fastapi import APIRouter, Query

from app.core.constants import PAGE_SIZE
from app.dtos.community_dtos.Community_list_response import CursorListResponse
from app.services.community_services.community_get_service import service_list_posts_cursor

router = APIRouter(prefix="/api/community", tags=["Community · Post"])

SearchIn = Literal["title", "content", "title_content"]

@router.get("/post/all/list-cursor", response_model=CursorListResponse)
async def list_all_posts_cursor(
    q: Optional[str] = Query(None),
    search_in: SearchIn = Query("title_content", description="title | content | title_content"),
    cursor: Optional[int] = Query(None),
    limit: int = Query(PAGE_SIZE, ge=1, le=50),
    author_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    badge: Optional[Literal["모집중","모집완료"]] = Query(None, description="study 전용 배지 필터"),
):
    return await service_list_posts_cursor(
        category="all",
        q=q, search_in=search_in,
        cursor=cursor, limit=limit,
        author_id=author_id, date_from=date_from, date_to=date_to,
        badge=badge,
    )

