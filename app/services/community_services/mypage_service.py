from typing import Optional, List, Any, Dict, Literal
from fastapi import HTTPException
from app.models.community import PostModel, LikeModel, CategoryType, StudyApplicationModel

RequestCategory = Literal["all", "study", "free", "share"]

def next_cursor_by_items(items: List[dict], key: str) -> Optional[int]:
    return items[-1][key] if items else None


async def service_list_my_posts(
        *,
        user_id: int,
        category: RequestCategory = "all",
        cursor: Optional[int] = None,
        limit: int = 6
) -> Dict[str, Any]:

    qs = (
        PostModel
        .filter(user_id=user_id, is_active=True)
        .select_related("user")              # ← 작성자 조인
    )

    if category and category != "all":
        qs = qs.filter(category=category)    # ← Post 자체 필드이므로 'category'

    if cursor is not None:
        qs = qs.filter(id__lt=cursor)

    rows = await qs.order_by("-id").limit(limit)

    items = [{
        "id": r.id,
        "category": r.category,
        "title": r.title,
        "author_id": r.user_id,
        "author_nickname": (r.post.user.nickname if getattr(r.post, "user", None) else None),
        "views": r.view_count,
        "created_at":r.created_at,
    } for r in rows]

    return {
        "count": len(items),
        "next_cursor": next_cursor_by_items(items, key="id"),
        "items":items,
    }


async def service_list_my_likes(
    *,
    user_id: int,
    category: RequestCategory = "all",
    cursor: Optional[int] = None,
    limit: int = 6
) -> Dict[str, Any]:

    lq = (
        LikeModel
        .filter(user_id=user_id, post__is_active=True)  # 글 비활성 제외를 미리
        .select_related("post", "post__user")          # 조인으로 한 번에
    )

    if category != "all":
        lq = lq.filter(post__category=category)        # ← 관계 경유 필터

    if cursor is not None:
        lq = lq.filter(id__lt=cursor)                  # 커서는 like.id 기준

    likes = await lq.order_by("-id").limit(limit)

    items: List[Dict[str, Any]] = []
    for lk in likes:
        p = getattr(lk, "post", None)
        if not p:
            continue
        u = getattr(p, "user", None)
        items.append({
            "id": p.id,
            "category": p.category,
            "title": p.title,
            "author_id": p.user_id,
            "author_nickname": (u.nickname if u else None),
            "views": p.view_count,
            "created_at": p.created_at,
            "liked_at": lk.created_at,
        })

    next_cursor = likes[-1].id if likes else None
    return {"count": len(items), "next_cursor": next_cursor, "items": items}


async def service_list_my_study_recruitments(
    *,
    owner_id: int,
    post_id: int,
    status: Optional[str] = None,
    cursor: Optional[int] = None,
    limit: int = 5
) -> Dict[str, Any]:

    post = await PostModel.get_or_none(id=post_id, category=CategoryType.STUDY)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    if post.user_id != owner_id:
        raise HTTPException(status_code=403, detail="Not the owner of the post")

    qs = StudyApplicationModel.filter(post_id=post_id)
    if cursor is not None:
        qs=qs.filter(id__lt=cursor)

    rows = await (
        qs.select_related("user")
        .order_by("-id")
        .limit(limit)
    )

    items: List[Dict[str, Any]] = []
    for r in rows:
        items.append({
            "application_id": r.id,
            "applicant_id": r.user.id,
            "applicant_nickname": getattr(getattr(r, "user", None), "nickname", None),
            "status": r.status,
            "applied_at": r.created_at,
        })
    next_cursor = next_cursor_by_items(items, key="application_id")

    return {"count": len(items), "next_cursor": next_cursor, "items": items}


async def service_list_my_applications(
    *,
    user_id: int,
    status: Optional[str] = None,
    cursor: Optional[int] = None,
    limit: int = 5
) -> Dict[str, Any]:

    qs = StudyApplicationModel.filter(user_id=user_id)
    if cursor is not None:
        qs=qs.filter(id__lt=cursor)

    rows = await (
        qs.select_related("post", "post__user")
        .order_by("-id")
        .limit(limit)
    )

    items: List[Dict[str, Any]] = []
    for r in rows:
        p = getattr(r, "post", None)
        owner = getattr(p, "user", None) if p else None
        items.append({
            "application_id": r.id,
            "post_id": r.post_id,
            "post_title": getattr(p, "title", None),
            "post_category": "study",
            "owner_id": getattr(p, "user_id", None),
            "owner_nickname": getattr(owner, "nickname", None),
            "status": r.status,
            "applied_at": r.created_at,
            "updated_at": r.updated_at,
        })
    next_cursor = next_cursor_by_items(items, key="application_id")

    return {"count": len(items), "next_cursor": next_cursor, "items": items}


