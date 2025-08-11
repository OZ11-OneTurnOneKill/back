from fastapi import Header, HTTPException, status

class UserLite:
    def __init__(self, id: int): self.id = id

async def get_current_user_dev(x_user_id: int | None = Header(None, convert_underscores=False)):
    # 클라이언트가 X-User-Id: 123 형태로 보낸다고 가정
    if x_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-User-Id header required")
    return UserLite(id=x_user_id)
