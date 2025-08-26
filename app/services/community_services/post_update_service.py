from typing import Dict, Any
from fastapi import HTTPException
from app.models.community import PostModel
from app.services.community_services.community_post_service import (
    service_update_study_post,
    service_update_free_post,
    service_update_share_post,
)

async def service_update_post(*, post_id: int, user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    카테고리 공통 PATCH 디스패처.
    - DB에서 post.category 확인 → 해당 카테고리 서비스로 위임
    - payload는 body.model_dump(exclude_unset=True) 그대로 넣고,
      카테고리별 서비스가 알아서 필요한 것만 사용하도록 둡니다.
    """
    post = await PostModel.get_or_none(id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    cat = post.category

    if cat == "study":
        # study 전용 필드들도 payload에 있으면 전달됨
        return await service_update_study_post(post_id=post_id, user_id=user_id, **payload)

    elif cat == "free":
        # title/content만 의미 있음 (여유 있으면 dict 필터링 해도 됨)
        allowed = {k: v for k, v in payload.items() if k in ("title", "content")}
        if not allowed:
            # 아무 필드도 안 남았다면 서비스가 400을 던지도록 그냥 넘겨도 되고,
            # 여기서 직접 400을 던져도 됩니다.
            pass
        return await service_update_free_post(post_id=post_id, user_id=user_id, **allowed)

    elif cat == "share":
        allowed = {k: v for k, v in payload.items() if k in ("title", "content")}
        return await service_update_share_post(post_id=post_id, user_id=user_id, **allowed)

    else:
        # 혹시 모를 확장 대비
        raise HTTPException(status_code=400, detail=f"Unsupported category: {cat}")