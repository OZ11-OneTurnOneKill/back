from fastapi import APIRouter, Query

from app.services.community_services.view_service import service_weekly_top5

router = APIRouter(prefix="/api/community", tags=["Community · Top"])

@router.get("/post/study/top-weekly")
async def top_weekly_study(limit: int = Query(5, ge=1, le=20)):
    return await service_weekly_top5(category="study", limit=limit)


@router.get("/post/free/top-weekly")
async def top_weekly_free(limit: int = Query(5, ge=1, le=20)):
    return await service_weekly_top5(category="free", limit=limit)


@router.get("/post/share/top-weekly")
async def top_weekly_share(limit: int = Query(5, ge=1, le=20)):
    return await service_weekly_top5(category="share", limit=limit)