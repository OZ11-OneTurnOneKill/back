from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query

from app.dtos.community_dtos.mypage_response import ApplicantListResponse, MyApplicationListResponse
from app.services.community_services.mypage_service import service_list_my_posts, service_list_my_likes, \
    service_list_my_study_recruitments, service_list_my_applications
from app.services.users.users import get_current_user


router = APIRouter(prefix="/api/v1/users", tags=["My Page"])

@router.get("/myinfo/posts")
async def my_posts(
        category: Literal["all", "study", "free", "share"] = Query("all"),
        cursor: Optional[int] = Query(None),
        limit: int = Query(6, ge=1, le=30),
        user = Depends(get_current_user),
):
    return await service_list_my_posts(user_id=user.id, category=category, cursor=cursor, limit=limit)


@router.get("/myinfo/likes")
async def my_likes(
        category: Literal["all", "study", "free", "share"] = Query("all"),
        cursor: Optional[int] = Query(None),
        limit: int = Query(6, ge=1, le=30),
        user = Depends(get_current_user),
):
    return await service_list_my_likes(user_id=user.id, category=category, cursor=cursor, limit=limit)


@router.get("/myinfo/{post_id}/applications", response_model=ApplicantListResponse) # 신청자 목록
async def my_applicants(
        post_id: int,
        status: Optional[Literal["approved", "rejected"]] = Query(None),
        cursor: Optional[int] = Query(None),
        limit: int = Query(5, ge=1, le=30),
        current_user = Depends(get_current_user)
):
    return await service_list_my_study_recruitments(
        owner_id=current_user.id,
        post_id=post_id,
        status=status,
        cursor=cursor,
        limit=limit,
    )

@router.get("/myinfo/applications", response_model=MyApplicationListResponse) # 신청 결과
async def my_list_applications(
        status: Optional[Literal["approved", "rejected"]] = Query(None),
        cursor: Optional[int] = Query(None),
        limit: int = Query(5, ge=1, le=30),
        current_user = Depends(get_current_user)
):
    return await service_list_my_applications(
        user_id=current_user.id,
        status=status,
        cursor=cursor,
        limit=limit,
    )