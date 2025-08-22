from typing import Optional, Literal, Union
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, status
from app.core.constants import PAGE_SIZE
from app.dtos.community_dtos.Community_list_response import CursorListResponse
from app.dtos.community_dtos.community_request import PostCreateRequest, StudyPostCreate, FreePostCreate, \
    SharePostCreate, PostUpdateAny
from app.dtos.community_dtos.community_response import PostDetailResponse, StudyPostResponse, FreePostResponse, \
    SharePostResponse
from app.services.community_services.community_common_service import service_delete_post_by_post_id
from app.services.community_services.community_get_service import service_list_posts_cursor
from app.services.community_services.post_detail_service import service_get_post_detail
from app.services.community_services import community_post_service as post_svc
from app.services.community_services.post_update_service import service_update_post

router = APIRouter(prefix="/api/v1/community", tags=["Community · Post"])

RequestCategory = Literal["all", "study", "free", "share"]
SearchIn = Literal["title", "content", "title_content", "author"]

@router.get("/post/list", response_model=CursorListResponse)
async def list_posts_cursor(
    category: RequestCategory = Query("all", description="all | study | free | share"),
    q: Optional[str] = Query(None),
    search_in: SearchIn = Query("title_content", description="title | content | title_content | author"),
    cursor: Optional[int] = Query(None),
    limit: int = Query(PAGE_SIZE, ge=1, le=50),
    author_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    badge: Optional[Literal["모집중","모집완료"]] = Query(None, description="study 전용 배지 필터"),
):
    return await service_list_posts_cursor(
        category=category,
        q=q, search_in=search_in,
        cursor=cursor, limit=limit,
        author_id=author_id, date_from=date_from, date_to=date_to,
        badge=badge,
    )

@router.get("/post/{post_id:int}", response_model=PostDetailResponse)
async def get_post_detail(post_id: int):
    data = await service_get_post_detail(post_id)
    if not data:
        raise HTTPException(404, "Post not found")
    return data

@router.post("/post", response_model=PostDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_post(body: PostCreateRequest, user :int):
    try:
        if isinstance(body, StudyPostCreate):
            return await post_svc.service_create_study_post(
                user_id=user,
                title=body.title,
                content=body.content,
                recruit_start=body.recruit_start,
                recruit_end=body.recruit_end,
                study_start=body.study_start,
                study_end=body.study_end,
                max_member=body.max_member,
            )
        elif isinstance(body, FreePostCreate):
            return await post_svc.service_create_free_post(
                user_id=user,
                title=body.title,
                content=body.content,
            )
        elif isinstance(body, SharePostCreate):
            return await post_svc.service_create_share_post(
                user_id=user,
                title=body.title,
                content=body.content,
            )
        else:
            raise HTTPException(400, "Unsupported category")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch(
    "/post/{post_id:int}",
    response_model=Union[StudyPostResponse, FreePostResponse, SharePostResponse],
)
async def patch_post(
        post_id: int,
        body: PostUpdateAny,
        user: int,  # 실제 운영에선: current_user = Depends(get_current_user); user_id = current_user.id
):
    payload = body.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        return await service_update_post(post_id=post_id, user_id=user, payload=payload)
    except HTTPException:
        raise
    except Exception as e:
        # 서비스 내부에서 이미 적절히 HTTPException을 던지므로
        # 예기치 못한 에러만 400으로 래핑
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/post/{post_id}")
async def delete_post(post_id: int, user: int):
    return await service_delete_post_by_post_id(post_id=post_id, user_id=user)