from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from pytz import timezone
from tortoise.expressions import Q
from tortoise.functions import Count

from app.core.constants import PAGE_SIZE
from app.models.community import PostModel, StudyRecruitmentModel
from app.models.community import StudyApplicationModel, ApplicationStatus  # pending/approved/rejected

KST = timezone("Asia/Seoul")

RequestCategory = Literal["all", "study", "free", "share"]

def _make_next_cursor(items: List[dict]) -> Optional[int]:
    return items[-1]["id"] if items else None

def compute_recruit_badge(*, recruit_start, recruit_end, max_member: int, approved_count: int, now=None) -> Optional[str]:
    """
    배지는 모집 기간 내에서만 표시.
    - 정원 미만: '모집중'
    - 정원 이상: '모집완료'
    - 모집 기간 외: None
    """
    now = now or datetime.now(KST)
    if recruit_start <= now <= recruit_end:
        return "모집완료" if approved_count >= max_member else "모집중"
    return None

async def service_list_posts_cursor(
    *,
    category: RequestCategory = "all",
    q: Optional[str] = None,
    cursor: Optional[int] = None,
) -> Dict[str, Any]:
    # 1) 기본 쿼리
    qs = PostModel.all() if category == "all" else PostModel.filter(category=category)
    if cursor is not None:
        qs = qs.filter(id__lt=cursor)  # 최신 → 과거
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))

    posts = await qs.order_by("-id").limit(PAGE_SIZE)

    # 2) 공통 요약 필드
    items = [{
        "id": p.id,
        "category": p.category,
        "title": p.title,
        "author_id": p.user_id,
        "views": p.view_count,
        "created_at": p.created_at,
    } for p in posts]

    # 3) study에만 배지(모집중/모집완료) 붙이기
    study_ids = [it["id"] for it in items if it["category"] == "study"]
    if study_ids:
        # 모집 정보 배치 조회
        srs = await StudyRecruitmentModel.filter(post_id__in=study_ids)
        sr_map = {sr.post_id: sr for sr in srs}

        # 승인된 신청 수 집계
        approved_rows = await (
            StudyApplicationModel
            .filter(post_id__in=study_ids, status=ApplicationStatus.approved.value)
            .group_by("post_id")
            .annotate(approved=Count("id"))
            .values("post_id", "approved")
        )
        approved_map = {r["post_id"]: int(r["approved"]) for r in approved_rows}

        # 아이템에 배지/remaining 추가
        for it in items:
            if it["category"] != "study":
                continue
            sr = sr_map.get(it["id"])
            if not sr:
                continue
            approved = approved_map.get(it["id"], 0)
            badge = compute_recruit_badge(
                recruit_start=sr.recruit_start,
                recruit_end=sr.recruit_end,
                max_member=sr.max_member,
                approved_count=approved,
            )
            if badge is not None:
                it.update({
                    "badge": badge,                              # "모집중" | "모집완료"
                    "remaining": max(0, sr.max_member - approved),  # 옵션
                    "max_member": sr.max_member,                    # 옵션
                })

    return {
        "count": len(items),
        "next_cursor": _make_next_cursor(items),
        "items": items,
    }
