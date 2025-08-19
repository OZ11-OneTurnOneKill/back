from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.services.community_services.mypage_service import service_list_my_posts, service_list_my_likes
from app.services.users.users import get_current_user


router = APIRouter(prefix="/api/v1/users", tags=["My Page"])

@router.get("/myinfo/posts")
async def my_posts(
        cursor: Optional[int] = Query(None),
        limit: int = Query(6, ge=1, le=30),
        user = Depends(get_current_user),
):
    return await service_list_my_posts(user_id=user.id, cursor=cursor, limit=limit)


@router.get("/myinfo/likes")
async def my_likes(
        cursor: Optional[int] = Query(None),
        limit: int = Query(6, ge=1, le=30),
        user = Depends(get_current_user),
):
    return await service_list_my_likes(user_id=user.id, cursor=cursor, limit=limit)