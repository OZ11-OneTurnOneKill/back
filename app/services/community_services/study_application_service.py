from fastapi import HTTPException
from tortoise.transactions import in_transaction
from app.models.community import PostModel, StudyApplicationModel, NotificationModel, ApplicationStatus

def _compose_app(app: StudyApplicationModel) -> dict:
    return {
        "id": app.id,
        "post_id": app.post_id,
        "user_id": app.user_id,
        "status": app.status,
        "created_at": app.created_at,
        "updated_at": app.updated_at,
    }

async def service_apply_to_study(*, post_id: int, user_id: int, message: str | None) -> dict:
    async with in_transaction() as tx:
        post = await PostModel.get_or_none(id=post_id, category="study").using_db(tx)
        if not post:
            raise HTTPException(status_code=404, detail="Study post not found")

        exists = await StudyApplicationModel.get_or_none(post_id=post_id, user_id=user_id).using_db(tx)
        if exists:
            raise HTTPException(status_code=409, detail="Already applied")

        app = await StudyApplicationModel.create(
            post_id=post_id, user_id=user_id, status=ApplicationStatus.pending.value, using_db=tx
        )
        await NotificationModel.create(
            user_id=post.user_id, application_id=app.id,
            message=message or f"사용자 {user_id}가 스터디({post_id})에 신청했습니다.",
            using_db=tx,
        )
        # 재조회로 타임스탬프 최신화
        app = await StudyApplicationModel.get(id=app.id).using_db(tx)
    return _compose_app(app)

async def service_approve_application(*, application_id: int, owner_id: int) -> dict:
    async with in_transaction() as tx:
        app = await StudyApplicationModel.get_or_none(id=application_id).using_db(tx)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        post = await PostModel.get(id=app.post_id).using_db(tx)
        if post.user_id != owner_id:
            raise HTTPException(status_code=403, detail="Not the owner")

        app.status = ApplicationStatus.approved.value
        await app.save(using_db=tx)
        await NotificationModel.create(
            user_id=app.user_id, application_id=app.id,
            message=f"스터디({post.id}) 신청이 승인되었습니다.", using_db=tx
        )
    return _compose_app(app)

async def service_reject_application(*, application_id: int, owner_id: int) -> dict:
    async with in_transaction() as tx:
        app = await StudyApplicationModel.get_or_none(id=application_id).using_db(tx)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        post = await PostModel.get(id=app.post_id).using_db(tx)
        if post.user_id != owner_id:
            raise HTTPException(status_code=403, detail="Not the owner")

        app.status = ApplicationStatus.rejected.value
        await app.save(using_db=tx)
        await NotificationModel.create(
            user_id=app.user_id, application_id=app.id,
            message=f"스터디({post.id}) 신청이 거절되었습니다.", using_db=tx
        )
    return _compose_app(app)
