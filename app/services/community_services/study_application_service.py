from fastapi import HTTPException
from pytz import timezone
from datetime import datetime
from tortoise.transactions import in_transaction
from app.models.community import PostModel, StudyApplicationModel, ApplicationStatus, \
    StudyRecruitmentModel
from app.services.community_services.notification_service import notify_application, \
    create_application_status_notification, push_notification_ws

KST = timezone("Asia/Seoul")


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
            raise HTTPException(404, "Study post not found")
        if post.user_id == user_id:
            raise HTTPException(403, "Cannot apply to your own post")

        sr = await StudyRecruitmentModel.get_or_none(post_id=post_id).using_db(tx)
        if not sr:
            raise HTTPException(409, "Recruitment info missing")

        now = datetime.now(KST)
        if not (sr.recruit_start <= now <= sr.recruit_end):
            raise HTTPException(403, "Recruitment period closed")

        dup = await StudyApplicationModel.get_or_none(post_id=post_id, user_id=user_id).using_db(tx)
        if dup:
            raise HTTPException(409, "Already applied")

        approved_count = await StudyApplicationModel.filter(
            post_id=post_id, status=ApplicationStatus.approved.value
        ).using_db(tx).count()
        if approved_count >= sr.max_member:
            raise HTTPException(409, "Recruitment is full")

        app = await StudyApplicationModel.create(
            post_id=post_id,
            user_id=user_id,
            status=ApplicationStatus.pending.value,
            using_db=tx,
        )

    note_id = await notify_application(
        application_id=app.id,
        post_id=post_id,
        applicant_id=user_id,
    )

    return {
        "application_id": app.id,
        "post_id": post_id,
        "status": "pending",
        "notified": bool(note_id),
        "message": message or "신청이 접수되었습니다.",
    }

async def service_approve_application(*, application_id: int, owner_id: int) -> dict:
    note = None
    async with in_transaction() as tx:
        app = await StudyApplicationModel.get_or_none(id=application_id).using_db(tx)
        if not app:
            raise HTTPException(404, "Application not found")

        post = await PostModel.get(id=app.post_id).only("user_id").using_db(tx)
        if post.user_id != owner_id:
            raise HTTPException(403, "Not the owner")

        if app.status == ApplicationStatus.approved.value:
            raise HTTPException(409, "Already approved")
        if app.status == ApplicationStatus.rejected.value:
            raise HTTPException(409, "Already rejected")

        sr = await StudyRecruitmentModel.get_or_none(post_id=app.post_id).using_db(tx)
        if not sr:
            raise HTTPException(409, "Recruitment info missing")

        now = datetime.now(KST)
        if now > sr.recruit_end:
            raise HTTPException(403, "Recruitment period closed")

        approved_count = await StudyApplicationModel.filter(
            post_id=app.post_id, status=ApplicationStatus.approved.value
        ).using_db(tx).count()
        if approved_count >= sr.max_member:
            raise HTTPException(409, "Recruitment is full")

        app.status = ApplicationStatus.approved.value
        await app.save(using_db=tx)

        note = await create_application_status_notification(
            receiver_id=app.user_id,
            application_id=app.id,
            post_id=app.post_id,
            actor_id=owner_id,
            status="approved",
            using_db=tx,
        )

    if note:
        await push_notification_ws(note)
    return _compose_app(app)

async def service_reject_application(*, application_id: int, owner_id: int) -> dict:
    note = None
    async with in_transaction() as tx:
        app = await StudyApplicationModel.get_or_none(id=application_id).using_db(tx)
        if not app:
            raise HTTPException(404, "Application not found")

        post = await PostModel.get(id=app.post_id).only("user_id").using_db(tx)
        if post.user_id != owner_id:
            raise HTTPException(403, "Not the owner")

        if app.status == ApplicationStatus.approved.value:
            raise HTTPException(409, "Already approved")
        if app.status == ApplicationStatus.rejected.value:
            raise HTTPException(409, "Already rejected")

        app.status = ApplicationStatus.rejected.value
        await app.save(using_db=tx)

        note = await create_application_status_notification(
            receiver_id=app.user_id,
            application_id=app.id,
            post_id=app.post_id,   # ✅ 일관화
            actor_id=owner_id,
            status="rejected",
            using_db=tx,
        )

    if note:
        await push_notification_ws(note)
    return _compose_app(app)