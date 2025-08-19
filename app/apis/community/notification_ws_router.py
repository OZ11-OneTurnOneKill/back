from fastapi import APIRouter, WebSocket, Query, HTTPException
from starlette.websockets import WebSocketDisconnect
from tortoise.expressions import Q
from app.core.realtime import notification_broker
from app.models.community import NotificationModel


router = APIRouter(prefix="/api/v1/community", tags=["notification_WebSocket"])

@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket):
    params = websocket.query_params
    x_user_id = params.get("x_user_id")
    preload = params.get("preload", "10")

    # 2) 기본 검증 (핸드셰이크 거절은 close code로)
    if not x_user_id or not x_user_id.isdigit():
        await websocket.close(code=1008)  # Policy violation
        return
    try:
        preload_n = max(0, min(100, int(preload)))  # 과도한 preload 방지
    except ValueError:
        await websocket.close(code=1008)
        return

    user_id = int(x_user_id)

    # 3) 연결 수립
    await notification_broker.connect(user_id, websocket)

    # 4) 접속 직후, 과거 알림 몇 개 선전송
    recent = await (NotificationModel
                    .filter(user_id=user_id)
                    .order_by("-id")
                    .limit(preload_n))
    for n in reversed(recent):  # 오래된 것부터 순서대로
        await notification_broker.push(user_id, {
            "id": n.id,
            "application_id": n.application_id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at,
        })

    # 5) 연결 유지: 서버는 일방 푸시만, 클라이언트에서 ping 대용으로 보낼 수 있음
    try:
        while True:
            # 아무 것도 안 받아도 되지만, 연결 유지를 위해 대기
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        notification_broker.disconnect(user_id, websocket)