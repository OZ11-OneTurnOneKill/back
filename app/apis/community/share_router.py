from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from tortoise.exceptions import DoesNotExist
from app.core.dev_auth import get_current_user_dev
from app.models.community import PostModel, CategoryType
from app.dtos.community_dtos.community_request import SharePostRequest, SharePostUpdateRequest
from app.dtos.community_dtos.community_response import SharePostResponse
from app.services.community_services.community_get_service import service_list_posts_cursor
from app.services.community_services.community_post_service import service_update_share_post
from app.utils.post_mapper import to_share_response
from app.services.community_services import community_post_service as post_svc
from app.apis.community._state import KST, post_author_map, post_views

router = APIRouter(prefix="/api/community", tags=["Community · Share"])

@router.post("/post/share", response_model=SharePostResponse)
async def create_share_post(body: SharePostRequest):
    try:
        return await post_svc.service_create_share_post(
            user_id=body.user_id,
            title=body.title,
            content=body.content,
            file_url=body.file_url,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/post/share/list-cursor")
async def list_share_posts_cursor(
    q: str | None = Query(None),
    cursor: int | None = Query(None),
):
    return await service_list_posts_cursor(category="share", q=q, cursor=cursor)


@router.get("/post/share/{post_id}", response_model=SharePostResponse)
async def get_share_post(post_id: int):
    post = await PostModel.get_or_none(id=post_id, category=CategoryType.SHARE) \
                          .select_related("data_share")
    if not post:
        raise HTTPException(404, "Post not found")
    await PostModel.filter(id=post_id, category=CategoryType.SHARE) \
                   .update(view_count=post.view_count + 1)
    return to_share_response(post)

@router.patch("/post/share/{post_id}", response_model=SharePostResponse)
async def patch_share_post(
    post_id: int,
    body: SharePostUpdateRequest,
    current_user = Depends(get_current_user_dev),
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
