from typing import Optional
from tortoise.exceptions import DoesNotExist
from app.models.community import PostModel
from app.dtos.community_dtos.community_response import (
    StudyPostResponse, StudyRecruitmentResponse,
    FreePostResponse, FreeImageOut,
    SharePostResponse, ShareFileOut,
)

def to_study_response(p: PostModel) -> StudyPostResponse:
    """
    PostModel(+ study_recruitment, + user) -> StudyPostResponse
    라우터/서비스에서 select_related("study_recruitment", "user")를 붙여주는 걸 권장.
    """
    sr = getattr(p, "study_recruitment", None)

    return StudyPostResponse(
        id=p.id,
        title=p.title,
        content=p.content,
        category=p.category,
        author_id=p.user_id,
        author_nickname=getattr(getattr(p, "user", None), "nickname", None),
        views=p.view_count,
        like_count=p.like_count,
        comment_count=p.comment_count,
        study_recruitment=(
            StudyRecruitmentResponse(
                recruit_start=sr.recruit_start,
                recruit_end=sr.recruit_end,
                study_start=sr.study_start,
                study_end=sr.study_end,
                max_member=sr.max_member,
            ) if sr else None
        ),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )

async def to_free_response(post: PostModel) -> FreePostResponse:
    """
    PostModel(+ user, + free_images) -> FreePostResponse
    - 라우터에서: .prefetch_related("free_images").select_related("user") 권장
    - 여기서 values(...)로 DTO 리스트 구성
    """
    # 작성자 닉네임 접근 위해 user 프리로드가 가장 좋음
    # (안 되어 있어도 getattr로 안전하게 처리)
    rows = await post.free_images.all().order_by("-id").values(
        "id", "image_url", "mime_type", "size_bytes", "created_at"
    )
    images = [FreeImageOut(**r) for r in rows]

    return FreePostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        category="free",
        author_id=post.user_id,
        author_nickname=getattr(getattr(post, "user", None), "nickname", None),
        views=post.view_count,
        like_count=post.like_count,
        comment_count=post.comment_count,
        images=images,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )

async def to_share_response(p: PostModel) -> SharePostResponse:
    """
    PostModel(+ user, + share_files) -> SharePostResponse
    - 라우터에서: .prefetch_related("share_files").select_related("user") 권장
    """
    rows = await p.share_files.all().order_by("-id").values(
        "id", "file_url", "mime_type", "size_bytes", "created_at"
    )
    files = [ShareFileOut(**r) for r in rows]

    return SharePostResponse(
        id=p.id,
        title=p.title,
        content=p.content,
        category="share",
        author_id=p.user_id,
        author_nickname=getattr(getattr(p, "user", None), "nickname", None),
        views=p.view_count,
        like_count=p.like_count,
        comment_count=p.comment_count,
        files=files,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )
