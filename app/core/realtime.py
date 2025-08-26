from typing import Dict, Set, Any
from fastapi import WebSocket
import asyncio
import json


class NotificationBroker:
    def __init__(self) -> None:
        self.active: Dict[int, Set[WebSocket]] = {}

    async def connect(self, user_id: int, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(user_id, set()).add(ws)

    def disconnect(self, user_id: int, ws: WebSocket):
        conns = self.active.get(user_id)
        if not conns: return
        conns.discard(ws)
        if not conns:
            self.active.pop(user_id, None)

    async def push(self, user_id: int, data: dict):
        # 로그아웃 상태 시 무시
        conns = self.active.get(user_id)
        if not conns: return
        msg = json.dumps({"type": "notification", "payload": data}, default=str)
        dead = []
        for ws in list(conns):
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(user_id, ws)


notification_broker = NotificationBroker()
