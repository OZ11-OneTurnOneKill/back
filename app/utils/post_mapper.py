from __future__ import annotations
from typing import Optional
from app.models.community import PostModel  # 네 실제 Post 모델 경로로 변경
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


def to_free_response(p: PostModel) -> FreePostResponse:
    """PostModel -> FreePostResponse"""
    fb = getattr(p, "free_board", None)

    return FreePostResponse(
        id=p.id,
        title=p.title,
        content=p.content,
        category=p.category,
        author_id=p.user_id,
        views=p.view_count,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def to_share_response(p: PostModel) -> SharePostResponse:
    """PostModel(+ data_share) -> SharePostResponse"""
    ds = getattr(p, "data_share", None)

    return SharePostResponse(
        id=p.id,
        title=p.title,
        content=p.content,
        category=p.category,
        author_id=p.user_id,
        views=p.view_count,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )
