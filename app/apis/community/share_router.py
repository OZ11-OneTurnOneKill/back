from datetime import datetime
from typing import Optional, Literal
from app.core import s3
import os
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from tortoise.exceptions import DoesNotExist
from app.core.attach_limits import FILE_MIMES, FILE_EXTS, MAX_TOTAL_BYTES_PER_POST
from app.core.constants import PAGE_SIZE
from app.dtos.community_dtos.Community_list_response import CursorListResponse
from app.dtos.community_dtos.attachments import PresignResp, PresignReq, AttachReq, ShareFileItem
from app.models.community import PostModel, CategoryType
from app.dtos.community_dtos.community_request import SharePostRequest, SharePostUpdateRequest
from app.dtos.community_dtos.community_response import SharePostResponse
from app.services.community_services.attachment_service import delete_share_file, upload_share_file
from app.services.community_services.community_get_service import service_list_posts_cursor
from app.services.community_services.community_post_service import service_update_share_post
from app.services.community_services.view_service import service_increment_view
from app.services.users.users import get_current_user
from app.utils.post_mapper import to_share_response
from app.services.community_services import community_post_service as post_svc
from app.apis.community._state import KST, post_author_map, post_views

router = APIRouter(prefix="/api/v1/community", tags=["Community · Share"])

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
    post = await (
        PostModel
        .filter(id=post_id, category=CategoryType.SHARE)
        .prefetch_related("share_files")
        .first()
    )
    if not post:
        raise HTTPException(404, "Post not found")

    await service_increment_view(post_id=post_id, category="share")
    # 최신 view 재조회
    post = await (
        PostModel
        .filter(id=post_id, category=CategoryType.SHARE)
        .prefetch_related("share_files")
        .first()
    )
    return await to_share_response(post)

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


@router.post("/post/share/{post_id}/attachments/upload", response_model=ShareFileItem)
async def upload_share_file_api(
    post_id: int,
    file: UploadFile = File(..., description="pdf/docx", media_type="multipart/form-data"),
    user = Depends(get_current_user),
):
    return await upload_share_file(post_id=post_id, user_id=user.id, file=file)

@router.delete("/post/share/{post_id}/attachments/{file_id}")
async def delete_share_file_api(
    post_id: int,
    file_id: int,
    user = Depends(get_current_user),
):
    return await delete_share_file(post_id=post_id, user_id=user.id, file_id=file_id)