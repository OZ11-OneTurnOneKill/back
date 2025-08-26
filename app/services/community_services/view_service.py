from datetime import date, datetime, timedelta
from pytz import timezone
from fastapi import HTTPException
from tortoise.transactions import in_transaction
from tortoise.expressions import F
from tortoise.functions import Sum
from app.models.community import PostModel, PostViewDailyModel

KST = timezone("Asia/Seoul")

async def service_increment_view(*, post_id: int, category: str) -> None:
    today = datetime.now(KST).date()
    async with in_transaction() as tx:
        updated = await PostModel.filter(id=post_id, category=category, is_active=True)\
                                 .using_db(tx).update(view_count=F("view_count") + 1)
        if not updated:
            raise HTTPException(status_code=404, detail="Post not found")

        row = await PostViewDailyModel.filter(post_id=post_id, day=today).using_db(tx).first()
        if row:
            await PostViewDailyModel.filter(id=row.id).using_db(tx).update(views=F("views") + 1)
        else:
            await PostViewDailyModel.create(post_id=post_id, day=today, views=1, using_db=tx)

async def service_weekly_top5(*, category: str, limit: int = 5) -> dict:
    start_day = date.today() - timedelta(days=6)

    # 집계와 그룹바이를 먼저 하고, 마지막에 values() 호출
    rows = await (
        PostViewDailyModel
        .filter(day__gte=start_day, post__category=category)
        .group_by("post_id")
        .annotate(total=Sum("views"))
        .order_by("-total", "-post_id")
        .limit(limit)
        .values("post_id", "total")
    )

    ids = [r["post_id"] for r in rows]
    if not ids:
        return {"category": category, "count": 0, "items": []}

    posts = await PostModel.filter(id__in=ids)
    post_map = {p.id: p for p in posts}

    items = []
    for r in rows:
        p = post_map.get(r["post_id"])
        if not p:
            continue
        items.append({
            "post_id": p.id,
            "title": p.title,
            "category": p.category,
            "author_id": p.user_id,
            "total_views_7d": int(r["total"] or 0),
            "created_at": p.created_at,
        })

    return {"category": category, "count": len(items), "items": items}