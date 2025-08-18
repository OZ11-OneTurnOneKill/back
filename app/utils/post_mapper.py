from __future__ import annotations

from email.mime import image
from typing import Optional
from app.models.community import PostModel, FreeImageModel, ShareFileModel  # 네 실제 Post 모델 경로로 변경
from app.dtos.community_dtos.community_response import (
    StudyPostResponse, StudyRecruitmentResponse,
    FreePostResponse,
    SharePostResponse,
)


def to_study_response(p: PostModel) -> StudyPostResponse:
    """PostModel(+ study_recruitment) -> StudyPostResponse"""
    sr = getattr(p, "study_recruitment", None)

    return StudyPostResponse(
        id=p.id,
        title=p.title,
        content=p.content,
        category=p.category,
        author_id=p.user_id,
        views=p.view_count,
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
    image_items = [
        FreeImageModel(
            id=img.id,
            image_url=img.image_url,
            mime_type=img.mime_type,
            size_bytes=img.size_bytes,
        )
        async for img in post.free_images.all()
    ]
    return FreePostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        category="free",
        author_id=post.user_id,
        views=post.view_count,
        images=image_items,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


async def to_share_response(p: PostModel) -> SharePostResponse:
    files = [
        ShareFileModel(
            id=f.id,
            file_url=f.file_url,
            mime_type=f.mime_type,
            size_bytes=f.size_bytes,
        )
        async for f in p.share_files.all()
    ]
    return SharePostResponse(
        id=p.id,
        title=p.title,
        content=p.content,
        category="share",
        author_id=p.user_id,
        views=p.view_count,
        files=files,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )