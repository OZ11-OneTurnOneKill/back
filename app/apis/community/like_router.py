from fastapi import APIRouter, Depends
from app.core.dev_auth import current_user_dev
from app.services.community_services.community_common_service import (
    service_get_like_info,
    service_toggle_like_by_post_id,
)
from app.services.users.users import get_current_user

router = APIRouter(prefix="/api/v1/community", tags=["Community · Like"])

@router.get("/post/{post_id}/likes")
async def read_like_count(post_id: int):
    return await service_get_like_info(post_id=post_id)


@router.post("/post/{post_id}/like")
async def toggle_like(post_id: int, user: int):
    return await service_toggle_like_by_post_id(post_id=post_id, user_id=user)



