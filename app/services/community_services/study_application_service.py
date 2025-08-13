from fastapi import HTTPException
from mypy.server.astmerge import replace_nodes_in_ast
from pytz import timezone
from datetime import datetime
from tortoise.transactions import in_transaction
from app.models.community import PostModel, StudyApplicationModel, NotificationModel, ApplicationStatus, \
    StudyRecruitmentModel
from app.core.realtime import notification_broker, NotificationBroker


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
    note_payload = None
    async with in_transaction() as tx:
        post = await PostModel.get_or_none(id=post_id, category="study").using_db(tx)
        if not post:
            raise HTTPException(status_code=404, detail="Study post not found")
        if post.user_id == user_id:
            raise HTTPException(status_code=403, detail="Cannot apply to your own post")

        sr = await StudyRecruitmentModel.get_or_none(post_id=post_id).using_db(tx)
        if not sr:
            raise HTTPException(status_code=409, detail="Recruitment info missing")

        now = datetime.now(KST)
        if not (sr.recruit_start <= now <= sr.recruit_end):
            raise HTTPException(status_code=403, detail="Recruitment period closed")

        dup = await StudyApplicationModel.get_or_none(post_id=post_id, user_id=user_id).using_db(tx)
        if dup:
            raise HTTPException(status_code=409, detail="Already applied")

        # 정원체크(승인된 인원 수)
        approved_count = await StudyApplicationModel.filter(
            post_id=post_id, status=ApplicationStatus.approved.value).using_db(tx).count()
        if approved_count >= sr.max_member:
            raise HTTPException(status_code=409, detail="Recruitment is full")

        app = await StudyApplicationModel.create(
            post_id=post_id, user_id=user_id, status=ApplicationStatus.pending.value, using_db=tx
        )

        note = await NotificationModel.create(
            user_id=post.user_id, application_id=app.id,
            message=message or f"사용자 {user_id}가 스터디({post_id})에 신청했습니다.",
            using_db=tx,
        )

        note_payload = {
            "target_user_id": post.user_id,
            "data": {
                "id": note.id,
                "application_id": app.id,
                "message": note.message,
                "is_read": note.is_read,
                "created_at": note.created_at,
            }
        }

        # 타임스탬프 최신화
        app = await StudyApplicationModel.get(id=app.id).using_db(tx)

    if note_payload:
        try:
            await notification_broker.push(note_payload["target_user_id"], note_payload["data"])
        except Exception:
            pass

    return _compose_app(app)

async def service_approve_application(*, application_id: int, owner_id: int) -> dict:
    note_payload = None
    async with in_transaction() as tx:
        app = await StudyApplicationModel.get_or_none(id=application_id).using_db(tx)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        post = await PostModel.get(id=app.post_id).using_db(tx)
        if post.user_id != owner_id:
            raise HTTPException(status_code=403, detail="Not the owner")

        if app.status == ApplicationStatus.approved.value:
            raise HTTPException(status_code=409, detail="Already approved")
        if app.status == ApplicationStatus.rejected.value:
            raise HTTPException(status_code=409, detail="Already rejected")

        sr = await StudyRecruitmentModel.get_or_none(post_id=app.post_id).using_db(tx)
        if not sr:
            raise HTTPException(status_code=409, detail="Recruitment info missing")
        now = datetime.now(KST)
        if now > sr.recruit_end:
            raise HTTPException(status_code=403, detail="Recruitment period closed")

        approved_count = await StudyApplicationModel.filter(
            post_id=app.post_id, status=ApplicationStatus.approved.value
        ).using_db(tx).count()
        if approved_count >= sr.max_member:
            raise HTTPException(status_code=409, detail="Recruitment is full")

        app.status = ApplicationStatus.approved.value
        await app.save(using_db=tx)

        note = await NotificationModel.create(
            user_id=app.user_id, application_id=app.id,
            message=f"스터디({post.id}) 신청이 승인되었습니다.", using_db=tx
        )
        note_payload = {
            "target_user_id": app.user_id,
            "data": {
                "id": note.id,
                "application_id": app.id,
                "message": note.message,
                "is_read": note.is_read,
                "created_at": note.created_at,
            }
        }

    if note_payload:
        try:
            await notification_broker.push(note_payload["target_user_id"], note_payload["data"])
        except Exception:
            pass

    return _compose_app(app)

async def service_reject_application(*, application_id: int, owner_id: int) -> dict:
    """
    거절: 소유자 권한, 상태 전이 검사(pending→rejected만).
    알림: 신청자에게 생성 + 커밋 후 WS 푸시
    """
    note_payload = None
    async with in_transaction() as tx:
        app = await StudyApplicationModel.get_or_none(id=application_id).using_db(tx)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        post = await PostModel.get(id=app.post_id).using_db(tx)
        if post.user_id != owner_id:
            raise HTTPException(status_code=403, detail="Not the owner")

        if app.status == ApplicationStatus.approved.value:
            raise HTTPException(status_code=409, detail="Already approved")
        if app.status == ApplicationStatus.rejected.value:
            raise HTTPException(status_code=409, detail="Already rejected")

        app.status = ApplicationStatus.rejected.value
        await app.save(using_db=tx)

        note = await NotificationModel.create(
            user_id=app.user_id,
            application_id=app.id,
            message=f"스터디({post.id}) 신청이 거절되었습니다.",
            using_db=tx,
        )
        note_payload = {
            "target_user_id": app.user_id,
            "data": {
                "id": note.id,
                "application_id": app.id,
                "message": note.message,
                "is_read": note.is_read,
                "created_at": note.created_at,
            },
        }

    if note_payload:
        try:
            await notification_broker.push(note_payload["target_user_id"], note_payload["data"])
        except Exception:
            pass

    return _compose_app(app)
