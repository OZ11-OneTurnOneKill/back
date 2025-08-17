from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from pytz import timezone
from tortoise.expressions import Q
from tortoise.functions import Count

from app.core.constants import PAGE_SIZE
from app.models.community import PostModel, StudyRecruitmentModel, ShareFileModel, FreeImageModel
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
    author_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    # 카테고리 전용 필터
    badge: Optional[Literal["모집중", "모집완료"]] = None,  # study 전용
    has_image: Optional[bool] = None,  # free 전용
    has_file: Optional[bool] = None,  # share 전용
) -> Dict[str, Any]:
    # 1) 기본 쿼리
    qs = PostModel.all() if category == "all" else PostModel.filter(category=category)
    if cursor is not None:
        qs = qs.filter(id__lt=cursor)  # 최신 → 과거
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
    if author_id is not None:
        qs = qs.filter(user_id=author_id)
    if date_from is not None:
        qs = qs.filter(created_at__gte=date_from)
    if date_to is not None:
        qs = qs.filter(created_at__lt=date_to)

    posts = await qs.order_by("-id").limit(PAGE_SIZE)
    # 2) 공통 요약 필드
    items: List[Dict[str, Any]] = [{
        "id": p.id,
        "category": p.category,
        "title": p.title,
        "author_id": p.user_id,
        "views": p.view_count,
        "created_at": p.created_at,
    } for p in posts]

    # 3) study 배지(모집중/모집완료) 붙이기
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
                    "badge": b,                                 # "모집중" | "모집완료"
                    "remaining": max(0, sr.max_member - approved),  # (옵션)
                    "max_member": sr.max_member,                    # (옵션)
                })

        # (선택) 배지 필터 적용
        if category in ("all", "study") and badge in ("모집중", "모집완료"):
            items = [it for it in items if it.get("badge") == badge]

    # 4) free: 이미지 유무 필터
    if category in ("all", "free") and has_image is not None:
        free_ids = [it["id"] for it in items if it["category"] == "free"]
        if free_ids:
            rows = await FreeImageModel.filter(post_id__in=free_ids).values_list("post_id", "image_url")
            with_image = {pid for (pid, url) in rows if url}
            if has_image:
                items = [it for it in items if (it["category"] != "free") or (it["id"] in with_image)]
            else:
                items = [it for it in items if (it["category"] != "free") or (it["id"] not in with_image)]

    # 5) share: 파일 유무 필터
    if category in ("all", "share") and has_file is not None:
        share_ids = [it["id"] for it in items if it["category"] == "share"]
        if share_ids:
            rows = await ShareFileModel.filter(post_id__in=share_ids).values_list("post_id", "file_url")
            with_file = {pid for (pid, url) in rows if url}
            if has_file:
                items = [it for it in items if (it["category"] != "share") or (it["id"] in with_file)]
            else:
                items = [it for it in items if (it["category"] != "share") or (it["id"] not in with_file)]

    return {
        "count": len(items),
        "next_cursor": _make_next_cursor(items),
        "items": items,
    }
