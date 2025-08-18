from datetime import datetime, timedelta
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException, Depends, Query
from tortoise.exceptions import DoesNotExist
from app.core.constants import PAGE_SIZE
from app.core.dev_auth import get_current_user_dev
from app.dtos.community_dtos.Community_list_response import CursorListResponse
from app.models.community import PostModel, CategoryType
from app.dtos.community_dtos.community_request import (
    StudyPostRequest,
    StudyPostUpdateRequest,
    ApplicationResponse,
    ApplicationCreateRequest
)
from app.dtos.community_dtos.community_response import StudyPostResponse
from app.services.community_services.community_get_service import service_list_posts_cursor
from app.services.community_services.community_post_service import service_update_study_post
from app.services.community_services import community_post_service as post_svc
from app.services.community_services.study_application_service import service_apply_to_study, \
    service_approve_application, service_reject_application
from app.utils.post_mapper import to_study_response
from app.apis.community._state import (
    KST, post_author_map, recruit_end_cache, post_views, notification_manager
)

router = APIRouter(prefix="/api/community", tags=["Community · Study"])

SearchIn = Literal["title", "content", "title_content"]

@router.post("/post/study", response_model=StudyPostResponse)
async def create_study_post(body: StudyPostRequest):
    try:
        return await post_svc.service_create_study_post(
            user_id=body.user_id,
            title=body.title,
            content=body.content,
            recruit_start=body.recruit_start,
            recruit_end=body.recruit_end,
            study_start=body.study_start,
            study_end=body.study_end,
            max_member=body.max_member,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/post/study/list-cursor", response_model=CursorListResponse)
async def list_study_posts_cursor(
    q: Optional[str] = Query(None),
    search_in: SearchIn = Query("title_content"),
    cursor: Optional[int] = Query(None),
    limit: int = Query(PAGE_SIZE, ge=1, le=50),
    author_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    badge: Optional[Literal["모집중","모집완료"]] = Query(None),
):
    return await service_list_posts_cursor(
        category="study",
        q=q, search_in=search_in,
        cursor=cursor, limit=limit,
        author_id=author_id, date_from=date_from, date_to=date_to,
        badge=badge,
    )


@router.get("/post/study/{post_id}", response_model=StudyPostResponse)
async def get_study_post(post_id: int):
    post = await PostModel.get_or_none(id=post_id, category=CategoryType.STUDY) \
                          .select_related("study_recruitment")
    if not post:
        raise HTTPException(404, "Post not found")
    await PostModel.filter(id=post_id, category=CategoryType.STUDY) \
                   .update(view_count=post.view_count + 1)
    return to_study_response(post)

@router.patch("/post/study/{post_id}", response_model=StudyPostResponse)
async def patch_study_post(
    post_id: int,
    body: StudyPostUpdateRequest,
    current_user = Depends(get_current_user_dev)
):
    # 1) 실제로 보낸 필드만 추출 (부분 업데이트)
    payload = body.model_dump(exclude_unset=True)  # 필요 시 exclude_none=True도 추가 가능

    # 2) 빈 PATCH 방지
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")

    # 3) 서비스 호출 (post_id + user_id는 항상 전달, 변경 필드는 **payload로 한 번에)
    try:
        return await service_update_study_post(
            post_id=post_id,
            user_id=current_user.id,  # 가짜 인증 헤더 X-User-Id에서 주입
            **payload
        )
    except DoesNotExist:
        # 서비스 내부에서 DoesNotExist가 그대로 올라오는 경우 대비
        raise HTTPException(status_code=404, detail="Post not found")


@router.post("/post/{post_id}/study-application", response_model=ApplicationResponse)
async def apply_to_study(post_id: int, body: ApplicationCreateRequest, current_user=Depends(get_current_user_dev)):
    return await service_apply_to_study(post_id=post_id, user_id=current_user.id, message=body.message)

@router.post("/study-application/{application_id}/approve", response_model=ApplicationResponse)
async def approve_application(application_id: int, current_user=Depends(get_current_user_dev)):
    return await service_approve_application(application_id=application_id, owner_id=current_user.id)

@router.post("/study-application/{application_id}/reject", response_model=ApplicationResponse)
async def reject_application(application_id: int, current_user=Depends(get_current_user_dev)):
    return await service_reject_application(application_id=application_id, owner_id=current_user.id)