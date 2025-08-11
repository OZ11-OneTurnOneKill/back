from fastapi import APIRouter, HTTPException
from app.dtos.community_dtos.community_request import CommentRequest, LikeToggleRequest
from app.dtos.community_dtos.community_response import CommentResponse

from app.apis.community._state import (
    KST, post_author_map, post_views,
    post_likes, post_like_counts, notification_manager
)
from datetime import datetime

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

@router.post("/post/{post_id}/like")
async def toggle_like(post_id: int, body: LikeToggleRequest):
    user_id = body.user_id
    if (post_id, user_id) in post_likes:
        del post_likes[(post_id, user_id)]
        post_like_counts[post_id] = max(0, post_like_counts.get(post_id, 0) - 1)
        return {"post_id": post_id, "likes": post_like_counts[post_id], "liked": False}

    post_likes[(post_id, user_id)] = True
    post_like_counts[post_id] = post_like_counts.get(post_id, 0) + 1

    post_author_id = post_author_map.get(post_id)
    if post_author_id and post_author_id != user_id:
        notification_manager.send_notification(
            user_id=post_author_id,
            message=f"{user_id}번 사용자가 당신의 게시글({post_id})에 좋아요를 눌렀습니다."
        )
    return {"post_id": post_id, "likes": post_like_counts[post_id], "liked": True}

@router.delete("/post/{post_id}")
async def delete_post(post_id: int):
    if post_id not in post_author_map:
        raise HTTPException(404, "Post not found")

    # 상태 정리 (mock)
    post_author_map.pop(post_id, None)
    # recruit_end_cache, post_views, post_likes 등도 필요시 정리
    return {"id": post_id, "deleted": True}
