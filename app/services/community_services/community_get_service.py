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
    ApplicationStatus,   # approved/pending/rejected (badge 계산에 approved 사용)
)

KST = timezone("Asia/Seoul")

RequestCategory = Literal["all", "study", "free", "share"]
SearchIn = Literal["title", "content", "title_content", "author"]


def _make_next_cursor(items: List[dict]) -> Optional[int]:
    """무한스크롤 커서: 마지막 아이템의 id를 다음 커서로 사용"""
    return items[-1]["id"] if items else None


def compute_recruit_badge(
    *,
    recruit_start: datetime,
    recruit_end: datetime,
    max_member: int,
    approved_count: int,
    now: Optional[datetime] = None,
) -> Optional[str]:
    """
    배지 정책:
      - 모집 기간 내에서만 표시
      - approved_count >= max_member → '모집완료', 아니면 '모집중'
      - 모집 기간 외 → None
    """
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
    badge: Optional[Literal["모집중", "모집완료"]] = None,  # study 전용(또는 all에서 study에만 적용)
) -> Dict[str, Any]:
    # 1) 기본 쿼리 (카테고리 & 커서 & 검색 & 공통 필터)
    qs = PostModel.all() if category == "all" else PostModel.filter(category=category)

    if cursor is not None:
        qs = qs.filter(id__lt=cursor)  # 최신 → 과거

    if q:
        if search_in == "title":
            qs = qs.filter(title__icontains=q)
        elif search_in == "content":
            qs = qs.filter(content__icontains=q)
        elif search_in == "author":
            qs = qs.filter(user__nickname__icontains=q).select_related("user")
        else:  # "title_content"
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))

    if author_id is not None:
        qs = qs.filter(user_id=author_id)

    if date_from is not None:
        qs = qs.filter(created_at__gte=date_from)

    if date_to is not None:
        qs = qs.filter(created_at__lt=date_to)

    qs = qs.select_related("user")

    posts = await qs.order_by("-id").limit(limit)

    # 2) 공통 요약 필드 구성
    items: List[Dict[str, Any]] = [{
        "id": p.id,
        "category": p.category,
        "title": p.title,
        "author_id": p.user_id,
        "author_nickname": getattr(p, "user", None) and p.user.nickname,
        "views": p.view_count,
        "created_at": p.created_at,
    } for p in posts]

    # 3) study 배지(모집중/모집완료) 계산 & 필터
    study_ids = [it["id"] for it in items if it["category"] == "study"]
    if study_ids:
        # 모집 정보
        srs = await StudyRecruitmentModel.filter(post_id__in=study_ids)
        sr_map = {sr.post_id: sr for sr in srs}

        # 승인 수 집계
        approved_rows = await (
            StudyApplicationModel
            .filter(post_id__in=study_ids, status=ApplicationStatus.approved.value)
            .group_by("post_id")
            .annotate(approved=Count("id"))
            .values("post_id", "approved")
        )
        approved_map = {r["post_id"]: int(r["approved"]) for r in approved_rows}

        # 배지 붙이기
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
                    "badge": b,                                  # "모집중" | "모집완료"
                    "remaining": max(0, sr.max_member - approved),  # (옵션)
                    "max_member": sr.max_member,                    # (옵션)
                })

        # 배지 필터 적용(요청 시)
        if category in ("all", "study") and badge in ("모집중", "모집완료"):
            items = [it for it in items if it.get("badge") == badge]

    return {
        "count": len(items),
        "next_cursor": _make_next_cursor(items),
        "items": items,
    }
