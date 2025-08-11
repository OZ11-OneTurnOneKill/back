from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from tortoise.exceptions import DoesNotExist

from app.core.dev_auth import get_current_user_dev
from app.models.community import PostModel, CategoryType
from app.dtos.community_dtos.community_request import (
    StudyPostRequest,
    StudyPostUpdateRequest,
    StudyJoinRequest
)
from app.dtos.community_dtos.community_response import StudyPostResponse
from app.services.community_services.community_post_service import service_update_study_post
from app.services.community_services import community_post_service as post_svc
from app.utils.post_mapper import to_study_response
from app.apis.community._state import (
    KST, post_author_map, recruit_end_cache, post_views, notification_manager
)

router = APIRouter(prefix="/api/community", tags=["Community · Study"])

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

@router.post("/post/study/{post_id}/join")
async def join_study_post(post_id: int, body: StudyJoinRequest):
    now = datetime.now(KST)
    recruit_end_from_db = recruit_end_cache.get(post_id)
    if recruit_end_from_db and getattr(recruit_end_from_db, "tzinfo", None) is None:
        recruit_end_from_db = recruit_end_from_db.replace(tzinfo=KST)
    if recruit_end_from_db and recruit_end_from_db < now:
        raise HTTPException(403, "모집이 마감된 스터디입니다.")

    author_id = post_author_map.get(post_id)
    notification_manager.send_notification(
        user_id=author_id,
        message=f"{body.user_id}님이 스터디 {post_id}에 참여하였습니다."
    )
    return {"message": f"User {body.user_id} joined study {post_id}!"}
