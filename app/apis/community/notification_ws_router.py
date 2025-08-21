from fastapi import APIRouter, WebSocket, Query, HTTPException
from starlette.websockets import WebSocketDisconnect
from tortoise.expressions import Q
from app.core.realtime import notification_broker
from app.models.community import NotificationModel
from app.services.users.users import get_current_websocket

router = APIRouter(prefix="/api/v1/community", tags=["notification_WebSocket"])

@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket):
    # 1) 인증 (핸드셰이크 전에 쿠키 확인)
    try:
        user = await get_current_websocket(websocket)
    except WebSocketDisconnect:
        return

    # 2) preload 파라미터 파싱 (기본 10, 상한 100)
    preload_raw = websocket.query_params.get("preload", "10")
    try:
        preload_n = max(0, min(100, int(preload_raw)))
    except ValueError:
        await websocket.close(code=1008)  # Policy violation
        return

    # 3) 핸드셰이크 수락 및 브로커 등록
    await websocket.accept()  # ✨ 브로커가 accept를 내부에서 하지 않는다면 반드시 필요
    await notification_broker.connect(user.id, websocket)

    # 4) 접속 직후 최근 알림 선전송(오래된 것부터)
    recent = await (
        NotificationModel
        .filter(user_id=user.id)
        .order_by("-id")
        .limit(preload_n)
    )
    for n in reversed(recent):
        await notification_broker.push(user.id, {
            "id": n.id,
            "application_id": n.application_id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at,
        })

    # 5) 연결 유지 (클라이언트 ping 대용 텍스트 수신)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        notification_broker.disconnect(user.id, websocket)