"""
# app/services/users/login.py
JWT Token 관련된 로직을 작성한 파일.
"""
import jwt
from app.configs.base_config import Google, Tokens
from app.dtos.users import Token, TokenUserData
from app.models.user import UserModel, RefreshTokenModel
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException,status
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from typing import Annotated

google = Google()
token = Tokens()

SECRET_KEY = google.SECRET_KEY
ALGORITHM = "HS256"


# 토큰 생성 로직
def create_token(data: dict, expires_delta: timedelta | None = None):
    """
    JWT token 생성 로직.
    이 함수를 통해 token 생성할 수 있다.

    :param data: user data
    :param expires_delta:
    :return: 생성한 token 값
    """
    # timedelta,
    to_encode = data.copy() # 저장된 유저 데이터를 직접 건들지 않고, 복사본을 생성해서 사용

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta # 만료 시간
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15) # 만료 시간,

    to_encode.update({"exp": expire}) # 토큰 데이터 관련 업데이트

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) # 토큰 생성

    return encoded_jwt, expire

async def create_access(user:str):
    """
    create_token 함수를 사용해 access token을 발급 받는다.
    :param user: user data
    :return: JWT access token, 만료 시간
    """
    jwt_access, expires = create_token(
        data={"sub": user},
        expires_delta=timedelta(minutes=token.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return jwt_access, expires

async def create_refresh(user:str):
    """
    create_token 함수를 사용해 refresh token을 발급받는다.
    :param user: user data
    :return: JWT refresh token, 만료 시간
    """
    jwt_refresh, expires_at = create_token(
        data={"sub": user},
        expires_delta=timedelta(days=token.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return jwt_refresh, expires_at


async def save_refresh(userdata, jwt_refresh, expires_at):
    """
    JWT, refresh token 상태를 DB로 관리 합니다.
    유저가 로그인 할때 DB에 데이터 유무에 따라 새로운 레코드를 생성하거나, 기존 레코드를 수정합니다.
    """
    token_check = await RefreshTokenModel.filter(user_id=userdata.id).first() # 기존 레코드 조회
    print(f'현재 데이터 상태 {token_check}')

    if token_check is None: # 만약 DB에 저장된 데이터 없을시, 새로 생성
        new_data = await RefreshTokenModel.create(
            user_id=userdata.id,
            token=jwt_refresh,
            expires_at=expires_at,
            revoked=False
        )
        print(f'NEW DATA!!!!:) {new_data}')
    else:
        before_data = await RefreshTokenModel.filter(user_id=userdata.id).first() # 기존 레코드 조회
        print(f'이전 refresh token {before_data.revoked}')
        update_data = await RefreshTokenModel.filter(user_id=userdata.id).update(
            updated_at=datetime.now(timezone.utc),
            token=jwt_refresh,
            expires_at=expires_at,
            revoked=False
        )
        check_data = await RefreshTokenModel.filter(user_id=userdata.id).first()
        print(f'refresh token {check_data.revoked}')
        print(f'UPDATE!!!!:) {update_data}')


async def revoke_refresh(userdata):
    """
    로그아웃 시, refresh token 비활성화.
    DB에서 revoke = True로 업데이트.
    :param userdata: user data
    """
    await RefreshTokenModel.filter(user=userdata, revoked=False).update(revoked=True, updated_at=datetime.now(timezone.utc))

# token 유효성 검사
async def token_check(token):
    """
    access token 재발급 시, refresh 토큰 유효성 검사를 진행한다.
    :param token: user가 로그인 시 발급 받은 refresh token
    :return: user data 반환
    """
    credentials_exception = HTTPException( # 에러
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # 서명이 유효한지 검증
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'], options={'verify_signature': True})
        userdata = payload.get("sub") # payload: jwt에 들어가는 데이터, sub: 토큰 주인
        print(f'토큰 주인 : {userdata}')

        if userdata is None:
            raise credentials_exception
        token_data = TokenUserData(user=userdata)
        print(f'이건 뭐야? : {token_data}')

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired token")
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = await UserModel.filter(id=token_data.user).first() # 유저 정보 데이터 확인, 실제로 있는 유저인지 체크 (없을 경우 에러 출력)
    if user is None:
        raise credentials_exception
    return user # users 테이블에서 가져온 유저 정보


def decode_token(token: str):
    try:
        # payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'], options={'verify_signature': False})

        return payload
    except ExpiredSignatureError:
        return None  # 토큰 만료
    except InvalidTokenError:
        return None  # 유효하지 않은 토큰


async def update_token(user_data):
    """
    access token 재발급
    """
    # DB에서 Refresh Token 상태 검증
    refresh = await RefreshTokenModel.get(user_id=user_data, revoked=False)
    if not refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인 정보가 없습니다.")
    print(f'refresh token : {refresh.token}, {refresh.revoked}')

    # JWT 검증
    user = await token_check(refresh.token)
    print(user.nickname)

    print(f'userID : {user.id}, refresh.userID : {refresh.user_id}')


    if user.id != refresh.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='토큰 정보가 맞지 않습니다.')

    else:
        new_access, acc_expires = await create_access(str(refresh.user_id))
        # new_refresh, re_expires = await create_refresh(refresh.user_id)
        print(f'새로운 access token 발급 : {new_access}')
        # print(f'새로운 refresh token 발급 : {new_refresh}')

        # update_data = await RefreshTokenModel.filter(user_id=refresh.user_id).update(
        #     updated_at=datetime.now(timezone.utc),
        #     token=new_refresh,
        #     expires_at=re_expires,
        #     revoked=False
        # )

        # print(f'이전 refresh token : {refresh.token}')
        # print(f'새로운 refresh token : {new_refresh}')
        return new_access