import json
from datetime import datetime, timezone

import httpx
import random

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.dtos.users import User, GetMyInfo
from app.models.user import UserModel
from google.oauth2.credentials import Credentials
from app.services.users.login import user_check, decode_token


async def get_current_user(request: Request):
    """
    JWT 토큰을 통해 로그인한 유저를 검증한다.

    """
    # 쿠키에 저장된 토큰을 가져옴
    token = request.cookies.get("access_token")
    # 토큰 검증
    if not token:
        raise HTTPException( # 토큰이 없을 경우, 에러 발생
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='access token을 조회할 수 없습니다.'
        )

    payload = decode_token(token)
    print('payload', payload)

    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 access token 입니다.")

    user_id = payload.get('sub')
    print('user_id', user_id)
    user = await UserModel.get_or_none(id=user_id)
    print('user', user)
    if not user:
        raise HTTPException(status_code=404, detail='access token에 유저 정보가 없습니다.')

    return user

'''
Authorization 헤더 방식으로 구현.
쿠키 방식 사용으로 사용하지 않음.


security = HTTPBearer() # 토큰 헤더 받아옴 `fastapi.security / HTTPBearer

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    JWT 토큰을 이용해 로그인한 유저를 인증 및 정보를 리턴한다.
    :param credentials:
    :return:
    """
    token = credentials.credentials
    print('get_current_user, token', token)
    if token.startswith("Bearer "):
        token = token[7:]

    payload = decode_token(token)
    print('payload', payload)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")

    user_id = payload.get('sub')
    print('user_id', user_id)
    user = await UserModel.get_or_none(id=user_id)
    print('user', user)
    if not user:
        raise HTTPException(status_code=404, detail='데이터 없음')

    return user
'''

async def get_or_create_google(user_info):
    """
    회원가입 및 로그인한 유저의 데이터가 DB에 저장 되어있는지 확인을 통해
    기존의 저장된 데이터를 가져오거나, 새롭게 데이터를 저장한다.
    """
    # user_info는 구글에서 받은 유저 데이터 (dict)
    # 이메일이나 소셜계정 기준으로 유저 조회
    user = await UserModel.filter(email=user_info['email']).first()

    if not user: # 기존 데이터에 없을 경우, 새로운 유저 생성.
        base_nickname = '반가워요' # 기본 베이스 닉네임
        while True:
            random_suffix = random.randint(1000, 9999) # 랜덤으로 4자리 숫자를 출력, 기본 베이스 닉네임 뒤에 랜덤으로 생성된 숫자를 추가.
            create_nickname = f"{base_nickname}{random_suffix}"
            if not await UserModel.filter(nickname=create_nickname): # 유니크 설정 되어있는 닉네임, 중복 방지를 위한 DB 확인
                nickname = create_nickname # 없을 경우 닉네임으로 생성
                break

        user = await UserModel.create(
            provider='google',
            provider_id=user_info.get('id'),
            email=user_info.get('email'),
            nickname=nickname,
            profile_image_url=user_info.get('picture'),
            is_active=True,
            is_superuser=False,
        )
        print(f'새로운 유저 {user.nickname} 생성됨')
    else:
        print(f'기존 유저 {user.nickname} 가져옴')

    return user


async def get_or_create_kakao(user_info):
    """
    회원가입 및 로그인한 유저의 데이터가 DB에 저장 되어있는지 확인을 통해
    기존의 저장된 데이터를 가져오거나, 새롭게 데이터를 저장한다.
    """
    # user_info는 구글에서 받은 유저 데이터 (dict)
    # 이메일이나 소셜계정 기준으로 유저 조회
    user = await UserModel.filter(email=user_info['email']).first()

    if not user: # 기존 데이터에 없을 경우, 새로운 유저 생성.
        base_nickname = '반가워요' # 기본 베이스 닉네임
        while True:
            random_suffix = random.randint(1000, 9999) # 랜덤으로 4자리 숫자를 출력, 기본 베이스 닉네임 뒤에 랜덤으로 생성된 숫자를 추가.
            create_nickname = f"{base_nickname}{random_suffix}"
            if not await UserModel.filter(nickname=create_nickname): # 유니크 설정 되어있는 닉네임, 중복 방지를 위한 DB 확인
                nickname = create_nickname # 없을 경우 닉네임으로 생성
                break

        user = await UserModel.create(
            provider='google',
            provider_id=user_info.get('id'),
            email=user_info.get('email'),
            nickname=nickname,
            profile_image_url=user_info.get('picture'),
            is_active=True,
            is_superuser=False,
        )
        print(f'새로운 유저 {user.nickname} 생성됨')
    else:
        print(f'기존 유저 {user.nickname} 가져옴')

    return user


async def update_user(user, update_nickname):
    """
    처음 가입할때 랜덤으로 생성된 닉네임을 유저가 원하는 닉네임으로 변경할 수 있다.
    :param user: 유저 데이터
    :param: update, 변경하고자 하는 닉네임
    :return: 변경된 닉네임
    """

    # DB 상에서 변경하려고 하는 닉네임이 있는지 확인
    check_nickname = await UserModel.get_or_none(nickname=update_nickname)

    # 닉네임 중복 확인
    if check_nickname is not None and check_nickname.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='이미 사용 중인 닉네임 입니다.'
        )
    # 없을 경우 닉네임 변경
    info = await UserModel.filter(id=user.id).update(
        nickname=update_nickname,
        updated_at=datetime.now(timezone.utc),
    )

    return update_nickname