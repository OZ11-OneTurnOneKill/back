from fastapi import APIRouter, WebSocket, Query, HTTPException, Depends
from starlette.websockets import WebSocketDisconnect
from tortoise.expressions import Q
from app.core.realtime import notification_broker
from app.models.community import NotificationModel
from app.models.user import UserModel
from app.services.users.users import get_current_websocket

router = APIRouter(prefix="/api/v1/community", tags=["notification_WebSocket"])

@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket,
                           user: UserModel = Depends(get_current_websocket),):
    # 쿼리 파라미터 preload 파싱 (인증 성공한 다음에 accept)
    preload = websocket.query_params.get("preload", "10")
    try:
        preload_n = max(0, min(100, int(preload)))
    except ValueError:
        await websocket.close(code=1008)
        return

    # 핸드셰이크 수락
    await websocket.accept()

    user_id = user.id
    await notification_broker.connect(user_id, websocket)

    # 과거 알림 선전송 (오래된 것부터)
    recent = await (
        NotificationModel
        .filter(user_id=user_id)
        .order_by("-id")
        .limit(preload_n)
    )
    for n in reversed(recent):
        await notification_broker.push(user_id, {
            "id": n.id,
            "application_id": n.application_id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at,
        })

    try:
        while True:
            await websocket.receive_text()  # 클라 ping 용도로 아무거나 보내도 OK
    except WebSocketDisconnect:
        pass
    finally:
        notification_broker.disconnect(user_id, websocket)