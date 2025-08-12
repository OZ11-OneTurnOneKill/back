from datetime import datetime
from typing import Optional, Literal
from fastapi import APIRouter, Query
from app.services.community_services.community_get_service import service_list_posts_cursor

router = APIRouter(prefix="/api/community", tags=["Community · Post"])

# 전체 피드
@router.get("/post/all/list-cursor")
async def list_all_posts_cursor(
    q: Optional[str] = Query(None),
    cursor: Optional[int] = Query(None),
    author_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    badge: Optional[Literal["모집중","모집완료"]] = Query(None, description="study 전용"),
    has_image: Optional[bool] = Query(None, description="free 전용"),
    has_file: Optional[bool] = Query(None, description="share 전용"),
):
    return await service_list_posts_cursor(
        category="all", q=q, cursor=cursor,
        author_id=author_id, date_from=date_from, date_to=date_to,
        badge=badge, has_image=has_image, has_file=has_file,
    )

