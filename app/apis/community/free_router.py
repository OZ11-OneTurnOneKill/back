from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from tortoise.exceptions import DoesNotExist
from app.core.dev_auth import get_current_user_dev
from app.models.community import PostModel, CategoryType
from app.dtos.community_dtos.community_request import FreePostRequest, FreePostUpdateRequest
from app.dtos.community_dtos.community_response import FreePostResponse
from app.services.community_services.community_get_service import service_list_posts_cursor
from app.utils.post_mapper import to_free_response
from app.services.community_services import community_post_service as post_svc
from app.services.community_services.community_post_service import service_update_free_post
from app.apis.community._state import KST, post_author_map, post_views

router = APIRouter(prefix="/api/community", tags=["Community · Free"])

@router.post("/post/free", response_model=FreePostResponse)
async def create_free_post(body: FreePostRequest):
    try:
        return await post_svc.service_create_free_post(
            user_id=body.user_id,
            title=body.title,
            content=body.content,
            image_url=body.image_url,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/post/free/list-cursor")
async def list_free_posts_cursor(
    q: str | None = Query(None),
    cursor: int | None = Query(None),
):
    return await service_list_posts_cursor(category="free", q=q, cursor=cursor)


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