from fastapi import APIRouter, Query
from app.services.community_services.community_get_service import service_list_posts_cursor

router = APIRouter(prefix="/api/community", tags=["Community · Post"])

# 전체 피드
@router.get("/post/all/list-cursor")
async def list_all_posts_cursor(
    q: str | None = Query(None),
    cursor: int | None = Query(None),
):
    return await service_list_posts_cursor(category="all", q=q, cursor=cursor)

