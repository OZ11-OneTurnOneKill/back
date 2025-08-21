from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from pytz import timezone
from tortoise.expressions import Q
from tortoise.functions import Count

from app.core.constants import PAGE_SIZE
from app.models.community import (
    PostModel,
    StudyRecruitmentModel,
    StudyApplicationModel,
    ApplicationStatus,
)
# from app.models.user import UserModel  # ← 더 이상 직접 조회 안 하므로 불필요

KST = timezone("Asia/Seoul")

RequestCategory = Literal["all", "study", "free", "share"]
SearchIn = Literal["title", "content", "title_content", "author"]


def _make_next_cursor(items: List[dict]) -> Optional[int]:
    return items[-1]["id"] if items else None


def compute_recruit_badge(
    *,
    recruit_start: datetime,
    recruit_end: datetime,
    max_member: int,
    approved_count: int,
    now: Optional[datetime] = None,
) -> Optional[str]:
    now = now or datetime.now(KST)
    if recruit_start <= now <= recruit_end:
        return "모집완료" if approved_count >= max_member else "모집중"
    return None


async def service_list_posts_cursor(
    *,
    category: RequestCategory = "all",
    q: Optional[str] = None,
    search_in: SearchIn = "title_content",
    cursor: Optional[int] = None,
    limit: int = PAGE_SIZE,
    author_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    badge: Optional[Literal["모집중", "모집완료"]] = None,
) -> Dict[str, Any]:

    qs = PostModel.all() if category == "all" else PostModel.filter(category=category)

    if cursor is not None:
        qs = qs.filter(id__lt=cursor)

    if q:
        if search_in == "title":
            qs = qs.filter(title__icontains=q)
        elif search_in == "content":
            qs = qs.filter(content__icontains=q)
        elif search_in == "author":
            qs = qs.filter(user__nickname__icontains=q)
        else:  # "title_content"
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))

    if author_id is not None:
        qs = qs.filter(user_id=author_id)

    if date_from is not None:
        qs = qs.filter(created_at__gte=date_from)
    if date_to is not None:
        qs = qs.filter(created_at__lt=date_to)

    # user 조인을 한 번만
    qs = qs.select_related("user")

    posts = await qs.order_by("-id").limit(limit)

    items: List[Dict[str, Any]] = [{
        "id": p.id,
        "category": p.category,
        "title": p.title,
        "author_id": p.user_id,
        "author_nickname": getattr(p.user, "nickname", None),
        "views": p.view_count,
        "created_at": p.created_at,
    } for p in posts]

    # study 배지 계산
    study_ids = [it["id"] for it in items if it["category"] == "study"]
    if study_ids:
        srs = await StudyRecruitmentModel.filter(post_id__in=study_ids)
        sr_map = {sr.post_id: sr for sr in srs}

        approved_rows = await (
            StudyApplicationModel
            .filter(post_id__in=study_ids, status=ApplicationStatus.approved.value)
            .group_by("post_id")
            .annotate(approved=Count("id"))
            .values("post_id", "approved")
        )
        approved_map = {r["post_id"]: int(r["approved"]) for r in approved_rows}

        for it in items:
            if it["category"] != "study":
                continue
            sr = sr_map.get(it["id"])
            if not sr:
                continue
            approved = approved_map.get(it["id"], 0)
            b = compute_recruit_badge(
                recruit_start=sr.recruit_start,
                recruit_end=sr.recruit_end,
                max_member=sr.max_member,
                approved_count=approved,
            )
            if b is not None:
                it.update({
                    "badge": b,
                    "remaining": max(0, sr.max_member - approved),
                    "max_member": sr.max_member,
                })

        if category in ("all", "study") and badge in ("모집중", "모집완료"):
            items = [it for it in items if it.get("badge") == badge]

    return {
        "count": len(items),
        "next_cursor": _make_next_cursor(items),
        "items": items,
    }
