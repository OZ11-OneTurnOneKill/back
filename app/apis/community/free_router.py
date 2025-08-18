from datetime import datetime
from typing import Optional, Literal
import os
from fastapi import APIRouter, HTTPException, Depends, Query
from tortoise.exceptions import DoesNotExist
from app.core import s3
from app.core.constants import PAGE_SIZE
from app.core.attach_limits import IMAGE_MIMES, IMAGE_EXTS, MAX_TOTAL_BYTES_PER_POST
from app.core.dev_auth import get_current_user_dev, UserLite
from app.dtos.community_dtos.Community_list_response import CursorListResponse
from app.dtos.community_dtos.attachments import PresignResp, PresignReq, AttachReq
from app.models.community import PostModel, CategoryType
from app.dtos.community_dtos.community_request import FreePostRequest, FreePostUpdateRequest
from app.dtos.community_dtos.community_response import FreePostResponse
from app.services.community_services.attachment_service import attach_free_image, delete_free_image
from app.services.community_services.community_get_service import service_list_posts_cursor
from app.utils.post_mapper import to_free_response
from app.services.community_services import community_post_service as post_svc
from app.services.community_services.community_post_service import service_update_free_post
from app.apis.community._state import KST, post_author_map, post_views

router = APIRouter(prefix="/api/community", tags=["Community · Free"])

SearchIn = Literal["title", "content", "title_content"]

@router.post("/post/free", response_model=FreePostResponse)
async def create_free_post(body: FreePostRequest):
    try:
        return await post_svc.service_create_free_post(
            user_id=body.user_id,
            title=body.title,
            content=body.content,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/post/free/list-cursor", response_model=CursorListResponse)
async def list_free_posts_cursor(
    q: Optional[str] = Query(None),
    search_in: SearchIn = Query("title_content"),
    cursor: Optional[int] = Query(None),
    limit: int = Query(PAGE_SIZE, ge=1, le=50),
    author_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    return await service_list_posts_cursor(
        category="free",
        q=q, search_in=search_in,
        cursor=cursor, limit=limit,
        author_id=author_id, date_from=date_from, date_to=date_to,
    )


@router.get("/post/free/{post_id}", response_model=FreePostResponse)
async def get_free_post(post_id: int):
    post = await PostModel.get_or_none(id=post_id, category=CategoryType.FREE) \
                          .select_related("free_board")
    if not post:
        raise HTTPException(404, "Post not found")
    await PostModel.filter(id=post_id, category=CategoryType.FREE) \
                   .update(view_count=post.view_count + 1)
    return to_free_response(post)

@router.patch("/post/free/{post_id}", response_model=FreePostResponse)
async def patch_free_post(
    post_id: int,
    body: FreePostUpdateRequest,
    current_user = Depends(get_current_user_dev),
):
    payload = body.model_dump(exclude_unset=True)  # 안 보낸 필드 제외(=부분 업데이트)
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        return await service_update_free_post(
            post_id=post_id,
            user_id=current_user.id,
            **payload              # ← 보낸 것만 서비스로 전달
        )
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Post not found")


def _ext_of(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""

@router.post("/post/free/{post_id}/attachments/presigned", response_model=PresignResp)
async def presign_free_image(post_id: int, body: PresignReq, user: UserLite = Depends(get_current_user_dev)):
    post = await PostModel.get_or_none(id=post_id, category="free")
    if not post: raise HTTPException(404, "Post not found")
    if post.user_id != user.id: raise HTTPException(403, "Not the author")

    ext = _ext_of(body.filename)
    if ext not in IMAGE_EXTS or body.content_type not in IMAGE_MIMES:
        raise HTTPException(400, "Only jpg/png allowed with correct MIME")

    # 1파일 최대는 '게시글 총한도(10MB)' 이하로 presign (실제 총합 제한은 attach에서 최종확인)
    return s3.presigned_post_strict("free", body.filename, body.content_type, MAX_TOTAL_BYTES_PER_POST)

@router.post("/post/free/{post_id}/attachments/attach")
async def attach_free_image_api(post_id: int, body: AttachReq, user: UserLite = Depends(get_current_user_dev)):
    return await attach_free_image(post_id=post_id, user_id=user.id, key=body.key)

@router.delete("/post/free/{post_id}/attachments/{image_id}")
async def delete_free_image_api(post_id: int, image_id: int, user: UserLite = Depends(get_current_user_dev)):
    return await delete_free_image(post_id=post_id, user_id=user.id, image_id=image_id)