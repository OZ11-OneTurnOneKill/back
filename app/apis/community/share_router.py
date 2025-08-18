from datetime import datetime
from typing import Optional, Literal
from app.core import s3
import os
from fastapi import APIRouter, HTTPException, Depends, Query
from tortoise.exceptions import DoesNotExist

from app.core.attach_limits import FILE_MIMES, FILE_EXTS, MAX_TOTAL_BYTES_PER_POST
from app.core.constants import PAGE_SIZE
from app.dtos.community_dtos.Community_list_response import CursorListResponse
from app.dtos.community_dtos.attachments import PresignResp, PresignReq, AttachReq
from app.models.community import PostModel, CategoryType
from app.dtos.community_dtos.community_request import SharePostRequest, SharePostUpdateRequest
from app.dtos.community_dtos.community_response import SharePostResponse
from app.services.community_services.attachment_service import attach_share_file, delete_share_file
from app.services.community_services.community_get_service import service_list_posts_cursor
from app.services.community_services.community_post_service import service_update_share_post
from app.services.community_services.view_service import service_increment_view
from app.services.users.users import get_current_user
from app.utils.post_mapper import to_share_response
from app.services.community_services import community_post_service as post_svc
from app.apis.community._state import KST, post_author_map, post_views

router = APIRouter(prefix="/api/community", tags=["Community · Share"])

SearchIn = Literal["title", "content", "title_content"]

@router.post("/post/share", response_model=SharePostResponse)
async def create_share_post(body: SharePostRequest):
    try:
        return await post_svc.service_create_share_post(
            user_id=body.user_id,
            title=body.title,
            content=body.content
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/post/share/list-cursor", response_model=CursorListResponse)
async def list_share_posts_cursor(
    q: Optional[str] = Query(None),
    search_in: SearchIn = Query("title_content"),
    cursor: Optional[int] = Query(None),
    limit: int = Query(PAGE_SIZE, ge=1, le=50),
    author_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    return await service_list_posts_cursor(
        category="share",
        q=q, search_in=search_in,
        cursor=cursor, limit=limit,
        author_id=author_id, date_from=date_from, date_to=date_to,
    )


@router.get("/post/share/{post_id:int}", response_model=SharePostResponse)
async def get_share_post(post_id: int):
    post = await PostModel.get_or_none(id=post_id, category=CategoryType.SHARE) \
                          .select_related("data_share")
    if not post:
        raise HTTPException(404, "Post not found")
    await service_increment_view(post_id=post_id, category="share")
    return to_share_response(post)

@router.patch("/post/share/{post_id}", response_model=SharePostResponse)
async def patch_share_post(
    post_id: int,
    body: SharePostUpdateRequest,
    current_user = Depends(get_current_user),
):
    payload = body.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        return await service_update_share_post(
            post_id=post_id,
            user_id=current_user.id,
            **payload,                 # ← 보낸 것만 서비스로
        )
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Post not found")



def _ext_of(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""

@router.post("/post/share/{post_id}/attachments/presigned", response_model=PresignResp)
async def presign_share_file(post_id: int, body: PresignReq, user = Depends(get_current_user)):
    post = await PostModel.get_or_none(id=post_id, category="share")
    if not post: raise HTTPException(404, "Post not found")
    if post.user_id != user.id: raise HTTPException(403, "Not the author")

    ext = _ext_of(body.filename)
    if ext not in FILE_EXTS or body.content_type not in FILE_MIMES:
        raise HTTPException(400, "Only pdf/docx allowed with correct MIME")

    return s3.presigned_post_strict("share", body.filename, body.content_type, MAX_TOTAL_BYTES_PER_POST)

@router.post("/post/share/{post_id}/attachments/attach")
async def attach_share_file_api(post_id: int, body: AttachReq, user = Depends(get_current_user)):
    return await attach_share_file(post_id=post_id, user_id=user.id, key=body.key)

@router.delete("/post/share/{post_id}/attachments/{file_id}")
async def delete_share_file_api(post_id: int, file_id: int, user = Depends(get_current_user)):
    return await delete_share_file(post_id=post_id, user_id=user.id, file_id=file_id)