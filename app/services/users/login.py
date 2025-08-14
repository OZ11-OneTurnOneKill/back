import jwt
from app.configs.base_config import Google, Tokens
from app.dtos.users import Token, TokenUserData
from app.models.user import UserModel, RefreshTokenModel
from app.models import user
from app.models.user import UserModel
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException,status
from jwt.exceptions import InvalidTokenError
from typing import Annotated

google = Google()
token = Tokens()

SECRET_KEY = google.SECRET_KEY
ALGORITHM = "HS256"


# 토큰 생성 로직
def create_token(data: dict, expires_delta: timedelta | None = None):
    # timedelta,
    to_encode = data.copy() # 저장된 유저 데이터를 직접 건들지 않고, 복사본을 생성해서 사용

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta # 만료 시간
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15) # 만료 시간,

    to_encode.update({"exp": expire}) # 토큰 데이터 관련 업데이트

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) # 토큰 생성

    return encoded_jwt, expire


# 유저 검증, token 유효성 검사
async def user_check(token: str):
    credentials_exception = HTTPException( # 에러
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # 서명이 유효한지 검증
        userdata = payload.get("sub") # payload: jwt에 들어가는 데이터, sub: 토큰 주인
        if userdata is None:
            raise credentials_exception
        token_data = TokenUserData(user=userdata)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired token")
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = await UserModel.filter(id=token_data.user).first() # 유저 정보 데이터 확인, 실제로 있는 유저인지 체크 (없을 경우 에러 출력)
    if user is None:
        raise credentials_exception
    return user # users 테이블에서 가져온 유저 정보

async def create_access(user:str):
    return create_token(
        data={"sub": user},
        expires_delta=timedelta(minutes=token.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

async def create_refresh(user:str):
    jwt_refresh, expires_at = create_token(
        data={"sub": user},
        expires_delta=timedelta(days=token.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return jwt_refresh, expires_at

async def save_refresh(userdata, jwt_refresh, expires_at):
    await RefreshTokenModel.create(
        user = userdata,
        token = jwt_refresh,
        expires_at = expires_at,
        revoked = False
    )


