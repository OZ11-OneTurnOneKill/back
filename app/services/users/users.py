import json
import httpx
import random

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.dtos.users import User, GetMyInfo
from app.models.user import UserModel
from google.oauth2.credentials import Credentials

from app.services.users.login import user_check, decode_token

# profile data
# async def info(credentials: Credentials): # 구글API에 사용자 정보 요청
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             'https://www.googleapis.com/oauth2/v2/userinfo',
#             headers={'Authorization': f'Bearer {credentials.token}'}
#         )
#         # print('요청에 문제가 발생했습니다.')
#         response.raise_for_status() # 요청 실패할 경우, 예외 발생
#
#         user_info = response.json() # json으로 데이터 받아옴.
#
#         return user_info

security = HTTPBearer() # 토큰 헤더 받아옴

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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

# async def get_cookie_access(request: Request):
#     # token = request.cookies.get('access_token')
#     # print(token)
#      user_data= await get_current_user()
#     return

async def get_info(user : UserModel) -> GetMyInfo:
    # info = await UserModel.get(id=user_id)

    print(GetMyInfo(
        id=user.id,
        nickname=user.nickname,  # Social Account
        profile_image_url=user.profile_image_url,  # Social Account
        email=user.email,
    ))
    return GetMyInfo(
        id = user.id,
        nickname = user.nickname, # Social Account
        profile_image_url = user.profile_image_url,  # Social Account
        email = user.email,
    )




async def get_or_create_user(user_info):
    # user_info는 구글에서 받은 유저 데이터 (dict)
    # social_account는 SocialAccountModel 인스턴스

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


"""async def get_google_user_data(credentials: Credentials):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        response.raise_for_status()
        return response.json()"""


async def save_google_userdata(credentials: Credentials):
    # 구글 유저 데이터 가져오기
    async with httpx.AsyncClient() as client:
        url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        response = await client.get(
            url,
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        response.raise_for_status()
        user_info = response.json()

        user = await get_or_create_user(user_info)

    return user

