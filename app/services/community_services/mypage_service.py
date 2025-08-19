from typing import Optional, List, Any, Dict
from app.models.community import PostModel, LikeModel


def next_cursor_by_items(items: List[dict], key: str) -> Optional[int]:
    return items[-1][key] if items else None


async def service_list_my_posts(*, user_id: int, cursor: Optional[int] = None, limit: int = 6) -> Dict[str, Any]:
    qs = PostModel.filter(user_id=user_id, is_active=True)
    if cursor is not None:
        qs = qs.filter(id__lt=cursor)
    rows = await qs.order_by("-id").limit(limit)

    items = [{
        "id": p.id,
        "category": p.category,
        "title": p.title,
        "author_id": p.user_id,
        "views": p.view_count,
        "created_at":p.created_at,
    } for p in rows]

    return {
        "count": len(items),
        "next_cursor": next_cursor_by_items(items, key="id"),
        "items":items,
    }


async def service_list_my_likes(*, user_id: int, cursor: Optional[int] = None, limit: int = 6) -> Dict[str, Any]:
    lq = LikeModel.filter(user_id=user_id)
    if cursor is not None:
        lq = lq.filter(id__lt=cursor)
    likes = await lq.order_by("-id").limit(limit)

    post_ids = [lk.post_id for lk in likes]
    if not post_ids:
        return {"count": 0, "next_cursor": None, "items": []}

    posts = await PostModel.filter(id__in=post_ids, is_active=True)
    post_map = {p.id: p for p in posts}

    items: List[Dict[str, Any]] = []
    for lk in likes:
        p = post_map.get(lk.post_id)
        if not p:
            continue
        items.append({
            "id": p.id,
            "category": p.category,
            "title": p.title,
            "author_id": p.user_id,
            "created_at":p.created_at,
            "liked_at": lk.created_at,
        })

    next_cursor = likes[-1].id if likes else None
    return {"count": len(items), "next_cursor": next_cursor, "items": items}