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

KST = timezone("Asia/Seoul")

RequestCategory = Literal["all", "study", "free", "share"]
SearchIn = Literal["title", "content", "title_content", "author"]


def _make_next_cursor(items: List[dict]) -> Optional[int]: # 현재 페이지 아이템중 가장 마지막 항목의 id를 다음 페이지로 넘길 커서값으로 사용
    return items[-1]["id"] if items else None # items[-1]은 마지막 요소 / 페이지가 비면(데이터가 없으면) None으로 알려줌


def compute_recruit_badge( # 스터디 모집 배지 계산 함수
    *, # 키워드 전용 인자 강제
    recruit_start: datetime, # 모집 기간
    recruit_end: datetime,
    max_member: int, # 정원
    approved_count: int, # 승인된 지원자 수
    now: Optional[datetime] = None,
) -> Optional[str]:
    now = now or datetime.now(KST)
    if recruit_start <= now <= recruit_end: # 기간 내 일때 승인 수 가 정원보다 같거나 클경우 모집완료, 그외 모집중
        return "모집완료" if approved_count >= max_member else "모집중"
    return None # 기간 외 None


async def service_list_posts_cursor( # 게시글 목록 조회 서비스로직
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
    # 기본 쿼리셋 구성
    qs = PostModel.all() if category == "all" else PostModel.filter(category=category) # 카테고리가 all이면 전체를, 아니면 카테고리 조건으로 시작

    if cursor is not None: # 커서가 있으면 헌재 커서보다 작은 id만 조회
        qs = qs.filter(id__lt=cursor)

    if q: # 검색어 필터
        if search_in == "title": # incontains = 대소문자 구분 없이 부분 일치 검색
            qs = qs.filter(title__icontains=q)
        elif search_in == "content":
            qs = qs.filter(content__icontains=q)
        elif search_in == "author":
            qs = qs.filter(user__nickname__icontains=q) # 더블언더스코어는 조인 경로임 / 작성자 닉네임으로 검색 시 자동으로 Join User가 들어감
        else:  # "title_content"
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q)) # Q(a | b) = OR조건임, Tortoise의 Q객체를 이용해 복합 조건 명시힘

    if author_id is not None:
        qs = qs.filter(user_id=author_id)

    if date_from is not None:
        qs = qs.filter(created_at__gte=date_from)
    if date_to is not None:
        qs = qs.filter(created_at__lt=date_to)

    # user 조인을 한 번만 N+1방지
    qs = qs.select_related("user")

    posts = await qs.order_by("-id").limit(limit) # await = 실제 DB요청 실행 지점 / 최신글 우선(-id)으로 정렬 / 페이지 크기만큼만 가져옴

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
    study_ids = [it["id"] for it in items if it["category"] == "study"] # 스터디 글만 추려서 리스트 생성(아래 계산에 최적화)
    if study_ids: # 스터디 모집 정보를 한번에 가져와서 딕셔너리 맵으로 바꿈
        srs = await StudyRecruitmentModel.filter(post_id__in=study_ids)
        sr_map = {sr.post_id: sr for sr in srs}

        approved_rows = await ( # 스터디 모집 승인된 인원수를 게시글별로 집계
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
