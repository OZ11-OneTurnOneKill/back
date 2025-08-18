from datetime import datetime
from fastapi import HTTPException, status
from pytz import timezone
from typing import Optional
from tortoise.transactions import in_transaction
from tortoise.exceptions import DoesNotExist

from app.core.constants import MAX_STUDY_MEMBERS
from app.models.community import (
    PostModel,
    StudyRecruitmentModel,
    FreeImageModel,
    ShareFileModel, StudyApplicationModel, ApplicationStatus,
)

KST = timezone("Asia/Seoul")

def _bad_request(msg: str):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

def _aware_kst(dt: datetime | None) -> datetime | None:
    """naive로 들어오면 KST로 붙여서 반환"""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=KST)

# ---------- 내부 유틸: 응답 조립 ----------
async def service_compose_study_response(post: PostModel, sr: StudyRecruitmentModel) -> dict:
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": "study",
        "author_id": getattr(post, "user_id"),
        "views": post.view_count,
        "study_recruitment": {
            "recruit_start": sr.recruit_start,
            "recruit_end": sr.recruit_end,
            "study_start": sr.study_start,
            "study_end": sr.study_end,
            "max_member": sr.max_member,
        },
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }


async def service_compose_free_response(post: PostModel) -> dict:
    images = await FreeImageModel.filter(post_id=post.id)\
        .order_by("-id")\
        .values("id", "image_url", "mime_type", "size_bytes", "created_at")
    return {
        "id": post.id,
        "category": "free",
        "title": post.title,
        "content": post.content,
        "author_id": post.user_id,
        "views": post.view_count,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "images": images,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }


async def service_compose_share_response(post: PostModel) -> dict:
    files = await ShareFileModel.filter(post_id=post.id).order_by("-id").values(
        "id", "file_url", "mime_type", "size_bytes", "created_at"
    )
    return {
        "id": post.id,
        "category": "share",
        "title": post.title,
        "content": post.content,
        "author_id": post.user_id,
        "views": post.view_count,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "files": files,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }


# ---------- 생성(Create) ----------
async def service_create_study_post(
    *,
    user_id: int,
    title: str,
    content: str,
    recruit_start: datetime,
    recruit_end: datetime,
    study_start: datetime,
    study_end: datetime,
    max_member: int,
) -> dict:
    if not (1 <= max_member <= MAX_STUDY_MEMBERS):
        raise HTTPException(400, f"max_member must be between 1 and {MAX_STUDY_MEMBERS}")
    """
    posts + study_recruitments 1:1 생성 (트랜잭션)
    """
    async with in_transaction() as tx:
        post = await PostModel.create(
            user_id=user_id,
            title=title,
            content=content,
            category="study",
            view_count=0,
            like_count=0,
            comment_count=0,
            using_db=tx,
        )
        sr = await StudyRecruitmentModel.create(
            post_id=post.id,
            recruit_start=recruit_start,
            recruit_end=recruit_end,
            study_start=study_start,
            study_end=study_end,
            max_member=max_member,
            using_db=tx,
        )
    # 재조회 없이 in-memory 객체로 응답 조립
    return await service_compose_study_response(post, sr)


async def service_create_free_post(
    *,
    user_id: int,
    title: str,
    content: str
) -> dict:
    async with in_transaction() as tx:
        post = await PostModel.create(
            user_id=user_id,
            title=title,
            content=content,
            category="free",
            view_count=0,
            like_count=0,
            comment_count=0,
            using_db=tx,
        )
    return await service_compose_free_response(post)


async def service_create_share_post(*, user_id: int, title: str, content: str) -> dict:
    async with in_transaction() as tx:
        post = await PostModel.create(
            user_id=user_id,
            title=title,
            content=content,
            category="share",
            view_count=0,
            like_count=0,
            comment_count=0,
            using_db=tx,
        )
    return await service_compose_share_response(post)


# ---------- 조회(Read) + 조회수 증가 ----------
async def get_study_post_and_incr_views(post_id: int) -> dict:
    """
    스터디 상세 조회 + 조회수 1 증가 (DB 카운터)
    """
    async with in_transaction() as tx:
        try:
            post = await PostModel.get(id=post_id, category="study").using_db(tx)
        except DoesNotExist:
            raise
        # 조회수 증가
        await PostModel.filter(id=post_id).using_db(tx).update(
            view_count=post.view_count + 1
        )
        # 최신 값 반영 위해 다시 가져오기
        post = await PostModel.get(id=post_id).using_db(tx)
        sr = await StudyRecruitmentModel.get(post_id=post_id).using_db(tx)
    return await service_compose_study_response(post, sr)


async def get_free_post_and_incr_views(post_id: int) -> dict:
    async with in_transaction() as tx:
        post = await PostModel.get(id=post_id, category="free").using_db(tx)
        await PostModel.filter(id=post_id).using_db(tx).update(
            view_count=post.view_count + 1
        )
        post = await PostModel.get(id=post_id).using_db(tx)
        free = await FreeImageModel.get(post_id=post_id).using_db(tx)
    return await service_compose_free_response(post, free)


async def get_share_post_and_incr_views(post_id: int) -> dict:
    async with in_transaction() as tx:
        post = await PostModel.get(id=post_id, category="share").using_db(tx)
        await PostModel.filter(id=post_id).using_db(tx).update(
            view_count=post.view_count + 1
        )
        post = await PostModel.get(id=post_id).using_db(tx)
        share = await ShareFileModel.get(post_id=post_id).using_db(tx)
    return await service_compose_share_response(post, share)


async def service_update_study_post(
    *,
    post_id: int,
    user_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    recruit_start: Optional[datetime] = None,
    recruit_end: Optional[datetime] = None,
    study_start: Optional[datetime] = None,
    study_end: Optional[datetime] = None,
    max_member: Optional[int] = None,
) -> dict:
    # (A) 서비스 레벨에서도 한 번 더 방어
    if all(v is None for v in (title, content, recruit_start, recruit_end, study_start, study_end, max_member)):
        _bad_request("No fields to update")

    if max_member is not None and not (1 <= max_member <= 30):
        raise HTTPException(status_code=400, detail="max_member must be between 1 and 30")

    recruit_start = _aware_kst(recruit_start)
    recruit_end = _aware_kst(recruit_end)
    study_start = _aware_kst(study_start)
    study_end = _aware_kst(study_end)

    async with in_transaction() as tx:
        # 게시글 조회 + 권한 체크
        post = await PostModel.get_or_none(id=post_id, category="study").using_db(tx)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not the author")

        # 모집정보 조회 (없으면 404)
        sr = await StudyRecruitmentModel.get_or_none(post_id=post_id).using_db(tx)
        if not sr:
            raise HTTPException(status_code=404, detail="Recruitment not found")

        # 최종 값으로 머지(부분 업데이트 고려)
        new_recruit_start = recruit_start or sr.recruit_start
        new_recruit_end   = recruit_end   or sr.recruit_end
        new_study_start   = study_start   or sr.study_start
        new_study_end     = study_end     or sr.study_end

        # 날짜 일관성 검증
        if not (new_recruit_start <= new_recruit_end <= new_study_start <= new_study_end):
            _bad_request("Invalid date range: recruit_start ≤ recruit_end ≤ study_start ≤ study_end")

        if max_member is not None:
            approved_count = await StudyApplicationModel.filter(
                post_id=post_id,
                status=ApplicationStatus.approved.value
            ).count()
            if max_member < approved_count:
                raise HTTPException(
                    status_code=409,
                    detail=f"cannot set max_member ({max_member}) below approved count ({approved_count})"
                )

        # 부분 업데이트 적용
        if title is not None:
            post.title = title
        if content is not None:
            post.content = content
        await post.save(using_db=tx)

        sr.recruit_start = new_recruit_start
        sr.recruit_end   = new_recruit_end
        sr.study_start   = new_study_start
        sr.study_end     = new_study_end
        if max_member is not None:
            sr.max_member = max_member
        await sr.save(using_db=tx)

    return await service_compose_study_response(post, sr)


async def service_update_free_post(
    *,
    post_id: int,
    user_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    image_url: Optional[str] = None,  # null을 보내면 삭제 의도(None 저장)로 처리
) -> dict:
    # 0) 빈 PATCH 방지
    if all(v is None for v in (title, content, image_url)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    async with in_transaction() as tx:
        # 1) 게시글 조회 + 권한
        post = await PostModel.get_or_none(id=post_id, category="free").using_db(tx)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not the author")

        # 2) 본문 부분 업데이트
        changed = False
        if title is not None:
            post.title = title
            changed = True
        if content is not None:
            post.content = content
            changed = True
        if changed:
            await post.save(using_db=tx)


    return await service_compose_free_response(post)


async def service_update_share_post(
    *,
    post_id: int,
    user_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    file_url: Optional[str] = None,   # null을 보내면 삭제 의도(None 저장)로 처리
) -> dict:
    # 0) 빈 PATCH 방지
    if all(v is None for v in (title, content, file_url)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    async with in_transaction() as tx:
        # 1) 게시글 조회 + 권한
        post = await PostModel.get_or_none(id=post_id, category="share").using_db(tx)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not the author")

        # 2) 본문 부분 업데이트
        changed = False
        if title is not None:
            post.title = title
            changed = True
        if content is not None:
            post.content = content
            changed = True
        if changed:
            await post.save(using_db=tx)


    return await service_compose_share_response(post)