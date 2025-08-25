from typing import Optional, Dict, Any, List

from app.core.realtime import notification_broker
from app.models.community import NotificationModel, NotificationType, PostModel


def _next_cursor(items: List[dict]) -> Optional[int]:
    return items[-1]["id"] if items else None

def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))

def _val(x):  # Enum/str 안전 변환 -> 항상 문자열로
    return getattr(x, "value", x)


async def service_list_notifications(
    *,
    user_id: int,
    cursor: Optional[int] = None,
    limit: int = 20,
    only_unread: bool = False,
    type_: Optional[str] = None,
) -> Dict[str, Any]:
    limit = _clamp(limit, 1, 50)

    qs = NotificationModel.filter(user_id=user_id)
    if only_unread:
        qs = qs.filter(is_read=False)

    if type_:
        norm = type_.strip().lower()
        if norm in ("like", "application"):
            qs = qs.filter(type=norm)  # CharEnumField면 str로 OK
        else:
            # 알 수 없는 타입이면 그냥 필터 미적용(또는 400을 던지도록 바꿔도 됨)
            pass

    if cursor is not None:
        qs = qs.filter(id__lt=cursor)

    rows = await (
        qs.select_related("actor", "post")   # N+1 방지
          .order_by("-id")
          .limit(limit)
    )

    items = []
    for n in rows:
        items.append({
            "id": n.id,
            "type": _val(n.type),                 # ← 일관적으로 문자열
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at,
            "post_id": n.post_id,
            "application_id": getattr(n, "application_id", None),
            "actor_id": getattr(n, "actor_id", None),
            "actor_nickname": getattr(getattr(n, "actor", None), "nickname", None),
        })

    return {
        "count": len(items),
        "next_cursor": _next_cursor(items),
        "has_more": len(items) == limit,
        "items": items,
    }


async def service_mark_read(*, user_id: int, ids: list[int]) -> Dict[str, Any]:
    updated = await (
        NotificationModel
        .filter(user_id=user_id, id__in=ids, is_read=False)
        .update(is_read=True)
    )
    return {"updated": updated}


async def service_mark_all_read(*, user_id: int, up_to_id: Optional[int] = None) -> Dict[str, Any]:
    qs = NotificationModel.filter(user_id=user_id, is_read=False)
    if up_to_id is not None:
        qs = qs.filter(id__lte=up_to_id)
    updated = await qs.update(is_read=True)
    return {"updated": updated}


async def service_unread_count(*, user_id: int) -> Dict[str, int]:
    cnt = await NotificationModel.filter(user_id=user_id, is_read=False).count()
    return {"unread": cnt}


async def notify_like(*, post_id: int, actor_id: int) -> Optional[int]:
    """
    - 수신자: 글 작성자(Post.user_id)
    - actor: 좋아요 누른 유저
    - 자기 글이면 스킵
    - 같은 actor가 같은 글을 여러 번 '좋아요'해도 알림 중복 방지
    """
    post = await PostModel.get_or_none(id=post_id)
    if not post:
        return None

    receiver_id = post.user_id
    if receiver_id == actor_id:
        return None

    exists = await NotificationModel.filter(
        user_id=receiver_id,
        type=NotificationType.LIKE.value,
        post_id=post_id,
        actor_id=actor_id,
    ).exists()
    if exists:
        return None

    note = await NotificationModel.create(
        user_id=receiver_id,
        type=NotificationType.LIKE.value,   # Enum을 그대로 넣어도 되지만 value로 고정
        post_id=post_id,
        actor_id=actor_id,
        message="회원님의 글에 좋아요가 달렸어요.",
    )

    # 웹소켓 푸시(실패 무시)
    try:
        await notification_broker.push(receiver_id, {
            "id": note.id,
            "type": _val(note.type),          # ← 일관적으로 문자열
            "post_id": post_id,
            "actor_id": actor_id,
            "message": note.message,
            "is_read": note.is_read,
            "created_at": note.created_at,
        })
    except Exception:
        pass

    return note.id


async def notify_application(*, application_id: int, post_id: int, applicant_id: int) -> Optional[int]:
    post = await PostModel.get_or_none(id=post_id)
    if not post:
        return None
    receiver_id = post.user_id
    if receiver_id == applicant_id:
        return None

    note = await NotificationModel.create(
        user_id=receiver_id,
        type=NotificationType.APPLICATION.value,
        application_id=application_id,
        post_id=post_id,
        actor_id=applicant_id,
        message="새로운 스터디 신청이 도착했어요.",
    )

    try:
        await notification_broker.push(receiver_id, {
            "id": note.id,
            "type": _val(note.type),
            "post_id": post_id,
            "application_id": application_id,
            "actor_id": applicant_id,
            "message": note.message,
            "is_read": note.is_read,
            "created_at": note.created_at,
        })
    except Exception:
        pass

    return note.id


async def create_application_status_notification(
    *,
    receiver_id: int,           # 알림 받는 사람 (신청자)
    application_id: int,
    post_id: int,
    actor_id: int,              # 승인/거절한 사람(글 소유자)
    status: str,                # "approved" | "rejected"
    using_db=None,
) -> NotificationModel:
    msg = "스터디 신청이 승인되었습니다." if status == "approved" else "스터디 신청이 거절되었습니다."
    return await NotificationModel.create(
        user_id=receiver_id,
        application_id=application_id,
        post_id=post_id,
        actor_id=actor_id,
        type=NotificationType.APPLICATION.value,  # ← 문자열로 저장 고정
        message=msg,
        using_db=using_db,
    )


async def push_notification_ws(note: NotificationModel) -> None:
    try:
        await notification_broker.push(note.user_id, {
            "id": note.id,
            "type": _val(note.type),
            "post_id": note.post_id,
            "application_id": note.application_id,
            "actor_id": note.actor_id,
            "message": note.message,
            "is_read": note.is_read,
            "created_at": note.created_at,
        })
    except Exception:
        pass
