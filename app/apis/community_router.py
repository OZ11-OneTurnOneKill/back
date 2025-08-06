from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from app.dtos.community_dtos.community_request import (
    StudyPostRequest,
    FreePostRequest,
    SharePostRequest,
    # CommonPostRequest,
    StudyPostUpdateRequest,
    CommentRequest
)
from app.dtos.community_dtos.community_response import (
    StudyPostResponse,
    FreePostResponse,
    SharePostResponse,
    # CommonPostResponse,
    CommentResponse
)
router = APIRouter(prefix="/api/community", tags=["Community"])


# @router.post("/post", response_model=CommonPostResponse)
# async def create_post(body: CommonPostRequest):
#     return {
#         "title": body.title,
#         "content": body.content,
#         "category": body.category,
#     }

# 조회수 캐시 (카테고리, post_id) 기준
post_views = {}


# ===== 스터디 모집 =====
@router.post("/post/study", response_model=StudyPostResponse)
async def create_study_post(body: StudyPostRequest):
    now = datetime.now()
    key = ("study", 1)
    post_views[key] = 0

    return {
        "id": 1,
        "title": body.title,
        "content": body.content,
        "category": body.category,
        "author_id": 123,
        "views": post_views[key],
        "study_recruitment": {
            "recruit_start": body.recruit_start,
            "recruit_end": body.recruit_end,
            "study_start": body.study_start,
            "study_end": body.study_end,
            "max_member": body.max_member,
        },
        "created_at": now,
        "updated_at": now,
    }


@router.get("/post/study/{post_id}", response_model=StudyPostResponse)
async def get_study_post(post_id: int):
    now = datetime.now()
    key = ("study", post_id)

    # 현재 조회수 가져오기
    current_views = post_views.get(key, 0) + 1
    post_views[key] = current_views

    return {
        "id": post_id,
        "title": "스터디 모집",
        "content": "테스트용 스터디",
        "category": "study",
        "author_id": 123,
        "views": current_views,   # ✅ 여기서만 증가된 값 반환
        "study_recruitment": {
            "recruit_start": now - timedelta(days=1),
            "recruit_end": now + timedelta(days=5),
            "study_start": now + timedelta(days=10),
            "study_end": now + timedelta(days=20),
            "max_member": 5,
        },
        "created_at": now,
        "updated_at": now,
    }


@router.put("/post/study/{post_id}", response_model=StudyPostResponse)
async def update_study_post(post_id: int, body: StudyPostUpdateRequest):
    now = datetime.now()
    recruit_end_from_db = now - timedelta(days=5)

    if recruit_end_from_db < now:
        raise HTTPException(
            status_code=403, detail="구인 기간이 끝난 스터디는 수정할 수 없습니다"
        )

    key = ("study", post_id)
    views = post_views.get(key, 0)

    return {
        "id": post_id,
        "title": body.title or "기존 제목",
        "content": body.content or "기존 내용",
        "category": "study",
        "author_id": 123,
        "views": views,
        "study_recruitment": {
            "recruit_start": body.recruit_start or now,
            "recruit_end": body.recruit_end or (now + timedelta(days=7)),
            "study_start": body.study_start or (now + timedelta(days=10)),
            "study_end": body.study_end or (now + timedelta(days=20)),
            "max_member": body.max_member or 5,
        },
        "created_at": now,
        "updated_at": now,
    }


@router.post("/post/study/{post_id}/join")
async def join_study_post(post_id: int, body: dict):
    now = datetime.now()
    recruit_end_from_db = now - timedelta(days=5)

    if recruit_end_from_db < now:
        raise HTTPException(
            status_code=403, detail="구인 기간이 끝난 스터디는 참여할 수 없습니다"
        )

    return {"message": f"user {body['user_id']} joined study {post_id}"}


# ===== 자유게시판 =====
@router.post("/post/free", response_model=FreePostResponse)
async def create_free_post(body: FreePostRequest):
    now = datetime.now()
    key = ("free", 2)
    post_views[key] = 0

    return {
        "id": 2,
        "title": body.title,
        "content": body.content,
        "category": body.category,
        "author_id": 123,
        "views": post_views[key],
        "free_board": {"image_url": body.image_url},
        "created_at": now,
        "updated_at": now,
    }


# ===== 자료공유 =====
@router.post("/post/share", response_model=SharePostResponse)
async def create_share_post(body: SharePostRequest):
    now = datetime.now()
    key = ("share", 3)
    post_views[key] = 0

    return {
        "id": 3,
        "title": body.title,
        "content": body.content,
        "category": body.category,
        "author_id": 123,
        "views": post_views[key],
        "data_share": {"file_url": body.file_url},
        "created_at": now,
        "updated_at": now,
    }


# ===== 댓글 =====
@router.post("/post/{post_id}/comment", response_model=CommentResponse)
async def create_comment(post_id: int, body: CommentRequest):
    now = datetime.now()
    return {
        "id": 1,
        "post_id": post_id,
        "content": body.content,
        "author_id": 123,
        "parent_id": body.parent_id,
        "created_at": now,
        "updated_at": now,
    }
