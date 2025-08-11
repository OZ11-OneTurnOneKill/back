from fastapi import APIRouter, HTTPException, Depends
from app.core.dev_auth import get_current_user_dev
from app.dtos.community_dtos.community_request import CommentRequest, LikeToggleRequest
from app.dtos.community_dtos.community_response import CommentResponse
from app.apis.community._state import (
    KST, post_author_map, post_views,
    post_likes, post_like_counts, notification_manager
)
from datetime import datetime
from app.services.community_services.community_common_service import (
    service_get_like_count_by_post_id,
    service_toggle_like_by_post_id,
    service_like_status,
    service_delete_post_by_post_id
)

router = APIRouter(prefix="/api/community", tags=["Community · Common"])

@router.post("/post/{post_id}/comment", response_model=CommentResponse)
async def create_comment(post_id: int, body: CommentRequest):
    now = datetime.now(KST)
    if post_id not in post_author_map:
        raise HTTPException(404, "Post not found")
    return {
        "id": 1,
        "post_id": post_id,
        "content": body.content,
        "author_id": 123,
        "parent_id": body.parent_id,
        "created_at": now,
        "updated_at": now,
    }

@router.get("/post/{post_id}/likes")
async def read_like_count(post_id: int):
    return await service_get_like_count_by_post_id(post_id=post_id)

@router.post("/post/{post_id}/like")
async def toggle_like(post_id: int, current_user = Depends(get_current_user_dev)):
    return await service_toggle_like_by_post_id(post_id=post_id, user_id=current_user.id)

@router.get("/post/{post_id}/like/status")
async def like_status(post_id: int, current_user = Depends(get_current_user_dev)):
    return await service_like_status(post_id=post_id, user_id=current_user.id)

@router.delete("/post/{post_id}")
async def delete_post(post_id: int, current_user = Depends(get_current_user_dev)):
    return await service_delete_post_by_post_id(post_id=post_id, user_id=current_user.id)
