import os
from fastapi import Depends, HTTPException, Request, WebSocket, status
from app.models.user import UserModel
from app.services.users.users import get_current_user  # 네가 쓰는 실제 함수 경로

ALLOW_FAKE = os.getenv("ALLOW_FAKE_AUTH") == "1"

async def current_user_dev(request: Request):
    """
    1) 실제 쿠키 인증 시도
    2) 실패했고, ALLOW_FAKE_AUTH=1이면 헤더/쿼리의 x-user-id로 가짜 인증 허용
    """
    # 1) 진짜 쿠키 인증 먼저 시도
    try:
        return await get_current_user(request)
    except HTTPException:
        pass

    # 2) 개발모드: 헤더/쿼리로 임시 사용자 주입
    if ALLOW_FAKE:
        uid = request.headers.get("x-user-id") or request.query_params.get("x_user_id")
        if uid and uid.isdigit():
            user = await UserModel.get_or_none(id=int(uid))
            if user:
                return user
            raise HTTPException(status_code=404, detail="fake user not found")
    # 개발모드 아니면 그대로 401
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


# WebSocket용 (쿠키 → 실패시 x_user_id)
async def current_user_ws_dev(ws: WebSocket):
    # 1) 쿠키 인증 시도
    token = ws.cookies.get("access_token")
    if token:
        # 네가 쓰는 decode + 조회 로직 재사용
        try:
            user = await get_current_user(ws)  # get_current_user가 Request 전용이면 아래 방식으로:
        except Exception:
            user = None
        else:
            if user:
                return user

    # 2) 개발모드: 쿼리로 가짜 인증
    if ALLOW_FAKE:
        x_uid = ws.query_params.get("x_user_id")
        if x_uid and x_uid.isdigit():
            user = await UserModel.get_or_none(id=int(x_uid))
            if user:
                return user

    # 실패 시 핸드셰이크 거절
    await ws.close(code=4401)  # 4401 Unauthorized
    return None
