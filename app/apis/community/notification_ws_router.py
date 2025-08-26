from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body, WebSocket, status
from starlette.websockets import WebSocketDisconnect
from app.models.user import UserModel
# 서비스 레이어
from app.services.community_services.study_application_service import (
    service_approve_application,
    service_reject_application,
)
from app.services.community_services.notification_service import (
    service_list_notifications,
    service_mark_read,
    service_mark_all_read,
    service_unread_count,
    push_notification_ws,  # ws 브로커 유틸
)
from app.models.community import NotificationModel
from app.core.realtime import notification_broker
from app.services.users.users import get_current_websocket, get_current_user

router = APIRouter(prefix="/api/v1/community", tags=["Notifications & Applications"])

# -----------------------------
# 1) 알림 목록/읽음/개수 REST
# -----------------------------

@router.get("/notifications")
async def list_notifications(
    user: int,
    cursor: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    only_unread: bool = Query(False),
    # current_user: UserModel = Depends(get_current_user),
):
    """
    알림 무한스크롤 목록.
    - cursor: 마지막으로 받은 알림 id 를 넣으면 그 이전 페이지
    - limit: 1~100
    - only_unread: 안읽은 것만 보기
    """
    return await service_list_notifications(
        user_id=user,
        # user_id=current_user.id,
        cursor=cursor,
        limit=limit,
        only_unread=only_unread,
    )


@router.post("/notifications/read")
async def mark_read(
    user: int,
    body: dict = Body(..., example={"ids": [101, 100, 99]}),
    # current_user: UserModel = Depends(get_current_user),
):
    """
    특정 알림 id 들을 읽음 처리.
    body: { "ids": [int, int, ...] }
    """
    ids = body.get("ids") or []
    if not ids or not all(isinstance(x, int) for x in ids):
        raise HTTPException(400, "ids must be a non-empty int array")
    return await service_mark_read(user_id=user, ids=ids) #user_id=current_user.id


@router.post("/notifications/read/all")
async def mark_all_read(
    user: int,
    up_to_id: Optional[int] = Query(None, description="특정 id 이하만 일괄 읽음 처리"),
    # current_user: UserModel = Depends(get_current_user),
):
    """
    (옵션) up_to_id 이하 전부 읽음 처리. 없으면 전체 읽음.
    """
    return await service_mark_all_read(user_id=user, up_to_id=up_to_id) #user_id=current_user.id


@router.get("/notifications/unread-count")
async def unread_count(current_user: UserModel = Depends(get_current_user)):
    """안 읽은 알림 개수"""
    return await service_unread_count(user_id=current_user.id)


# -----------------------------------------
# 2) 스터디 신청 승인/거절 (알림은 서비스에서 처리)
# -----------------------------------------

@router.post("/applications/{application_id}/approve")
async def approve_application(
    application_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """
    글 소유자가 신청 승인.
    내부에서 알림 저장(+커밋 후 WS 푸시)까지 처리됨.
    """
    return await service_approve_application(
        application_id=application_id,
        owner_id=current_user.id,
    )


@router.post("/applications/{application_id}/reject")
async def reject_application(
    application_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """
    글 소유자가 신청 거절.
    내부에서 알림 저장(+커밋 후 WS 푸시)까지 처리됨.
    """
    return await service_reject_application(
        application_id=application_id,
        owner_id=current_user.id,
    )


# -----------------------------
# 3) 알림 웹소켓 (쿠키 인증)
# -----------------------------

@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket):
    """
    쿠키에 access_token 이 있어야 함.
    쿼리: preload=초기 로딩 개수(기본 10, 최대 100)
    """
    # 쿠키 기반 인증
    try:
        user: UserModel = await get_current_websocket(websocket)
    except Exception as e:
        # get_current_websocket 내부에서 WebSocketException(code=1008) 을 던지도록 구현돼 있다면
        # 여기까지 오지 않고 연결이 거절됨. 혹시 모를 예외는 안전하게 종료.
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 쿼리 파라미터
    preload_q = websocket.query_params.get("preload", "10")
    try:
        preload_n = max(0, min(100, int(preload_q)))
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 연결 수립
    await notification_broker.connect(user.id, websocket)

    # 최근 알림 선전송 (오래된 것부터)
    recent = await (
        NotificationModel
        .filter(user_id=user.id)
        .order_by("-id")
        .limit(preload_n)
    )
    for n in reversed(recent):
        await notification_broker.push(user.id, {
            "id": n.id,
            "type": getattr(n.type, "value", n.type),
            "post_id": getattr(n, "post_id", None),
            "application_id": getattr(n, "application_id", None),
            "actor_id": getattr(n, "actor_id", None),
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at,
        })

    # keep-alive (클라이언트가 ping 용으로 아무 문자열이나 보낼 수 있음)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        notification_broker.disconnect(user.id, websocket)
