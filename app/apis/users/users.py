import json
from app.services.users.users import get_info, get_current_user
from app.services.users.login import user_check
from fastapi import APIRouter, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.responses import RedirectResponse
from google.oauth2.credentials import Credentials


router = APIRouter(prefix='/api/v1/users', tags=['Users'])

security = HTTPBearer() # 토큰 헤더 받아옴

@router.get('/logintest')
async def now(request: Request):
    """
    로그인 상태 여부를 확인하는 라우터
    """
    # token = request.cookies.get('token')
    # check = await user_check(token)

    return f'로그인 일단 된듯'
@router.get('/myinfo')
async def get_myinfo(user = Depends(get_current_user)):
    return {'id': user.id, 'nickname': user.nickname, 'email': user.email}
    # return await get_info(user)
    # return '환영합니다:) 로그인 성공했습니다.'
    # return {
    #     "nickname": current_user.nickname,
    #     "profile_image_url": current_user.profile_image_url,
    #     "email": current_user.social_account.email if current_user.social_account else None,
    #     "provider": current_user.social_account.provider if current_user.social_account else None
    # }

"""async def get_myinfo(request:Request) -> dict:
    # session에 credentials 여부 확인
    credentials_check = request.session.get('credentials')

    if not credentials_check:  # 없을 경우, 에러 메세지 출력
        return {'msg': '세션에 사용자 관련 정보가 없습니다.'}
    # json으로 credentials 객체 만들기
    credentials = Credentials.from_authorized_user_info(json.loads(credentials_check))

    # 권한 여부 확인
    granted_scopes = credentials.scopes
    if 'https://www.googleapis.com/auth/userinfo.email' not in granted_scopes:
        return {'msg': '이메일 접근 권한이 없습니다.'}  # 없을 경우 메세지 출력
    if 'https://www.googleapis.com/auth/userinfo.profile' not in granted_scopes:
        return {'msg': '프로필 접근 권한이 없습니다.'}  # 없을 경우 메세지 출력

    user_info = await info(credentials)

    return user_info
"""
