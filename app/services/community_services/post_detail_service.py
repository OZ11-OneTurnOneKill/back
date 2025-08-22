from typing import Union
from tortoise.expressions import F
from app.models.community import PostModel, CategoryType
from app.utils.post_mapper import to_study_response, to_free_response, to_share_response
from app.services.community_services.view_service import service_increment_view

async def service_get_post_detail(post_id: int) -> Union[dict, ...]:
    # 1) 카테고리 판별
    base = await PostModel.get_or_none(id=post_id)
    if not base:
        return None

    # 2) 조회수 +1
    await service_increment_view(post_id=post_id, category=base.category)

    # 3) 카테고리별로 relation 붙여 재조회 & 매핑
    if base.category == CategoryType.STUDY:
        post = await (
            PostModel
            .filter(id=post_id)
            .select_related("user", "study_recruitment")
            .first()
        )
        return to_study_response(post)

    elif base.category == CategoryType.FREE:
        post = await (
            PostModel
            .filter(id=post_id)
            .select_related("user")
            .prefetch_related("free_images")
            .first()
        )
        return await to_free_response(post)

    elif base.category == CategoryType.SHARE:
        post = await (
            PostModel
            .filter(id=post_id)
            .select_related("user")
            .prefetch_related("share_files")
            .first()
        )
        return await to_share_response(post)

    # 알 수 없는 카테고리 방어
    return None
