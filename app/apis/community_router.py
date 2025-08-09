from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from pytz import timezone
from app.dtos.community_dtos.community_request import (
    StudyPostRequest,
    FreePostRequest,
    SharePostRequest,
    # CommonPostRequest,
    StudyPostUpdateRequest,
    CommentRequest,
    StudyJoinRequest,
    LikeToggleRequest
)
from app.dtos.community_dtos.community_response import (
    StudyPostResponse,
    FreePostResponse,
    SharePostResponse,
    # CommonPostResponse,
    CommentResponse
)
from app.services.community_services.notification_manager import notification_manager

router = APIRouter(prefix="/api/community", tags=["Community"])

KST = timezone("Asia/Seoul")

# @router.post("/post", response_model=CommonPostResponse)
# async def create_post(body: CommonPostRequest):
#     return {
#         "title": body.title,
#         "content": body.content,
#         "category": body.category,
#     }

# 조회수 캐시 (카테고리, post_id) 기준
posts_store = {}          # {post_id: dict}
post_author_map = {}      # {post_id: author_id}
post_views = {}           # {post_id: int}
post_likes = {}           # {(post_id, user_id): True}
post_like_counts = {}     # {post_id: int}
recruit_end_cache = {}    # {post_id: datetime}
# ===== 스터디 모집 =====
@router.post("/post/study", response_model=StudyPostResponse)
async def create_study_post(body: StudyPostRequest):
    now = datetime.now(KST)
    post_id = len(recruit_end_cache) + 1
    post_author_map[post_id] = body.user_id
    recruit_end_cache[post_id] = (
        KST.localize(body.recruit_end) if body.recruit_end.tzinfo is None else body.recruit_end
    )  #  항상 aware로 저장
    post_views[("study", post_id)] = 0

    return {
        "id": post_id,
        "title": body.title,
        "content": body.content,
        "category": body.category,
        "author_id": body.user_id,
        "views": post_views[("study", post_id)],
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
    now = datetime.now(KST)
    key = ("study", post_id)

    # 현재 조회수 가져오기
    current_views = post_views.get(key, 0) + 1
    post_views[key] = current_views
    # ✅ 작성자 ID 불러오기
    author_id = post_author_map.get(post_id)
    # ✅ 마감일도 불러오기 (옵션)
    recruit_end = recruit_end_cache.get(post_id, now + timedelta(days=5))

    return {
        "id": post_id,
        "title": "스터디 모집",
        "content": "테스트용 스터디",
        "category": "study",
        "author_id": author_id,
        "views": current_views,
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
    now = datetime.now(KST)
    recruit_end_from_db = recruit_end_cache.get(post_id, now + timedelta(days=5))

    if recruit_end_from_db and recruit_end_from_db.tzinfo is None:
        recruit_end_from_db = KST.localize(recruit_end_from_db)

    if recruit_end_from_db < now:
        raise HTTPException(
            status_code=403, detail="구인 기간이 끝난 스터디는 수정할 수 없습니다"
        )

    key = ("study", post_id)
    views = post_views.get(key, 0)
    author_id = post_author_map.get(post_id, 0)

    if body.recruit_end:
        recruit_end_cache[post_id] = (
            KST.localize(body.recruit_end) if body.recruit_end.tzinfo is None else body.recruit_end
        )
    return {
        "id": post_id,
        "title": body.title or "기존 제목",
        "content": body.content or "기존 내용",
        "category": "study",
        "author_id": author_id,
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
async def join_study_post(post_id: int, body: StudyJoinRequest):
    now = datetime.now(KST)
    recruit_end_from_db = recruit_end_cache.get(post_id)

    # recruit_end가 naive이면 KST로 localize
    if recruit_end_from_db is not None and recruit_end_from_db.tzinfo is None:
        recruit_end_from_db = KST.localize(recruit_end_from_db)

    if recruit_end_from_db is not None and recruit_end_from_db < now:
        raise HTTPException(status_code=403, detail="모집이 마감된 스터디입니다.")

    author_id = post_author_map.get(post_id)
    notification_manager.send_notification(
        user_id=author_id,
        message=f"{body.user_id}님이 스터디 {post_id}에 참여하였습니다."
    )
    # 테스트용 응답
    return {"message": f"User {body.user_id} joined study {post_id}!"}

# ===== 자유게시판 =====
@router.post("/post/free", response_model=FreePostResponse)
async def create_free_post(body: FreePostRequest):
    now = datetime.now(KST)
    post_id = len(post_author_map) + 1
    post_author_map[post_id] = body.user_id
    # ✅ 조회수 초기화
    post_views[("free", post_id)] = 0

    return {
        "id": post_id,
        "title": body.title,
        "content": body.content,
        "category": body.category,
        "author_id": body.user_id,
        "views": post_views[("free", post_id)],
        "free_board": {"image_url": body.image_url},
        "created_at": now,
        "updated_at": now,
    }


# ===== 자료공유 =====
@router.post("/post/share", response_model=SharePostResponse)
async def create_share_post(body: SharePostRequest):
    now = datetime.now(KST)
    # ✅ post_id 생성 (auto-increment 방식)
    post_id = len(post_author_map) + 1
    # ✅ 작성자 ID 저장
    post_author_map[post_id] = body.user_id
    # ✅ 조회수 초기화
    post_views[("share", post_id)] = 0

    return {
        "id": post_id,
        "title": body.title,
        "content": body.content,
        "category": body.category,
        "author_id": body.user_id,
        "views": post_views[("share", post_id)],
        "data_share": {"file_url": body.file_url},
        "created_at": now,
        "updated_at": now,
    }


# ===== 댓글 =====
@router.post("/post/{post_id}/comment", response_model=CommentResponse)
async def create_comment(post_id: int, body: CommentRequest):
    now = datetime.now(KST)
    post_author_id = post_author_map.get(post_id)
    return {
        "id": 1,
        "post_id": post_id,
        "content": body.content,
        "author_id": 123,
        "parent_id": body.parent_id,
        "created_at": now,
        "updated_at": now,
    }


@router.post("/post/{post_id}/like")
async def toggle_like(post_id: int, body: LikeToggleRequest):
    user_id = body.user_id

    if (post_id, user_id) in post_likes:
        # 이미 좋아요 누른 상태면 → 취소
        del post_likes[(post_id, user_id)]
        post_like_counts[post_id] = max(0, post_like_counts.get(post_id, 0) - 1)
        return {
            "post_id": post_id,
            "likes": post_like_counts[post_id],
            "liked": False
        }

    # 좋아요 추가
    post_likes[(post_id, user_id)] = True
    post_like_counts[post_id] = post_like_counts.get(post_id, 0) + 1

    # ✅ 게시글 작성자 ID 가져오기 (예시: mock DB 기준)
    post_author_id = post_author_map.get(post_id)

    # ✅ 내가 아니라 작성자에게 알림 전송
    if post_author_id and post_author_id != user_id:
        notification_manager.send_notification(
            user_id=post_author_id,
            message=f"{user_id}번 사용자가 당신의 게시글({post_id})에 좋아요를 눌렀습니다."
        )

    return {
        "post_id": post_id,
        "likes": post_like_counts[post_id],
        "liked": True
    }


@router.put("/post/free/{post_id}", response_model=FreePostResponse)
async def update_free_post(post_id: int, body: FreePostRequest):
    if post_id not in post_author_map:
        raise HTTPException(status_code=404, detail="Post not found")

    key = ("free", post_id)
    views = post_views.get(key, 0)
    now = datetime.now(KST)

    author_id = post_author_map.get(post_id, body.user_id)

    return {
        "id": post_id,
        "title": body.title,
        "content": body.content,
        "category": "free",
        "author_id": author_id,
        "views": views,
        "free_board": {"image_url": body.image_url},
        "created_at": now,   # mock이라 그대로 now로
        "updated_at": now,
    }


@router.put("/post/share/{post_id}", response_model=SharePostResponse)
async def update_share_post(post_id: int, body: SharePostRequest):
    if post_id not in post_author_map:
        raise HTTPException(status_code=404, detail="Post not found")

    key = ("share", post_id)
    views = post_views.get(key, 0)
    now = datetime.now(KST)

    author_id = post_author_map.get(post_id, body.user_id)

    return {
        "id": post_id,
        "title": body.title,
        "content": body.content,
        "category": "share",
        "author_id": author_id,
        "views": views,
        "data_share": {"file_url": body.file_url},
        "created_at": now,
        "updated_at": now,
    }


@router.delete("/post/{post_id}")
async def delete_post(post_id: int):
    if post_id not in post_author_map:
        raise HTTPException(status_code=404, detail="Post not found")

    # 메인 식별자 존재하면 연결된 캐시/맵 정리
    post_author_map.pop(post_id, None)
    recruit_end_cache.pop(post_id, None)
    post_like_counts.pop(post_id, None)

    # views : 카테고리별 키 제거
    for cat in ("study", "free", "share"):
        post_views.pop((cat, post_id), None)

    # likes : (post_id, user_id) 전체 제거
    to_remove = [k for k in list(post_likes.keys()) if k[0] == post_id]
    for k in to_remove:
        post_likes.pop(k, None)

    return {"id": post_id, "deleted": True}