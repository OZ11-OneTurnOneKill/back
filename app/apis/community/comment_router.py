from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.dev_auth import current_user_dev
from app.dtos.community_dtos.community_request import CommentRequest, CommentUpdateRequest
from app.dtos.community_dtos.community_response import CommentResponse, CommentListResponse
from datetime import datetime
from app.services.community_services.community_common_service import (
    service_create_comment,
    service_list_comments,
    service_update_comment,
    service_delete_comment
)
from app.services.users.users import get_current_user

router = APIRouter(prefix="/api/v1/community", tags=["Community · Comment"])

@router.post("/post/{post_id}/comment", response_model=CommentResponse)
async def create_comment(
    user: int,
    post_id: int,
    body: CommentRequest,
    # current_user = Depends(current_user_dev),               # 헤더에서 user_id 주입
):
    return await service_create_comment(
        post_id=post_id,
        user_id=user,
        content=body.content,
        parent_comment_id=body.parent_comment_id,               # alias로 parent_id도 허용한 DTO라면 그대로 OK
    )


@router.get("/post/{post_id}/comments", response_model=CommentListResponse)
async def list_comments(
    post_id: int,
    order: str = Query("id", description="정렬: id(오래된순) | -id(최신순)"),
    offset: int = 0,
    limit: int = 50,
):
    return await service_list_comments(post_id=post_id, order=order, offset=offset, limit=limit)


@router.patch("/comment/{comment_id}", response_model=CommentResponse)
async def update_comment(
    user: int,
    comment_id: int,
    body: CommentUpdateRequest,
    # current_user = Depends(current_user_dev),   # X-User-Id
):
    return await service_update_comment(
        comment_id=comment_id,
        user_id=user,
        content=body.content,
    )

# 삭제: DELETE /comment/{comment_id}
@router.delete("/comment/{comment_id}")
async def delete_comment(
    user: int,
    comment_id: int,
    # current_user = Depends(current_user_dev),   # X-User-Id
):
    return await service_delete_comment(
        comment_id=comment_id,
        user_id=user,
    )




