from datetime import datetime, timedelta
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
    today = datetime.now(KST).date()
    start = today - timedelta(days=6)

    rows = await(
        PostViewDailyModel
        .filter(day__gte=start, day__lte=today, post__category=category, post__is_active=True)
        .group_by("post_id")
        .annotate(views7=Sum("views"))
        .order_by("-views7", "-post_id")
        .limit(limit)
        .values(
            "post_id",
            "views7",
            "post__title",
            "post__user_id",
            "post__created_at",
        )
    )

    items = [{
        "post_id": r["post_id"],
        "title": r["post__title"],
        "author_id": r["post__user_id"],
        "views_7d": int(r["views7"] or 0),
        "created_at": r["post__created_at"],
    } for r in rows]

    return {
        "category": category,
        "range": {"from": start.isoformat(), "to": today.isoformat()},
        "count": len(items),
        "items": items,
    }