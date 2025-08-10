import json
from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse

from app.dtos import users
from app.dtos.users import SocialAccountModel
from app.models import user
from app.services.google_login import create_authorization_url, access_token, info # revoke

from google.oauth2.credentials import Credentials

router = APIRouter(prefix="/api/v1/users/auth/google/login")


# OAuth2.0 액세스 토큰 가져오기
# app이 Google OAuth2.0 서버와 상호작용, 사용자를 대신해 API 요청을 실행하기 위한 동의를 받음.
# @router.post("auth/google/login")
# async def google_login_post()
@router.get("/", description='authorization_url 생성') # 로그인 및 권한 동의 페이지 URL 생성
async def get_authorization_url(request:Request) -> RedirectResponse:
    authorization_url = await create_authorization_url(request)
    return RedirectResponse(authorization_url)

@router.get("/callback", name='callback') # 구글에게 로그인 관련 데이터를 받음
async def get_access_token(request: Request) -> RedirectResponse: # access token 교환
    credentials = await access_token(request)
    print(f'콜백에서 받은 credentials : {credentials}')
    # features = check_granted_scopes(credentials)
    mypage_url = '/api/v1/users/auth/google/login/myinfo'
    return RedirectResponse(mypage_url)

"""
@router.post('/revoke')
async def post_revoke(request: Request) -> RedirectResponse:
    await revoke(request)
    return RedirectResponse(url='/')
"""

@router.get('/myinfo')
async def get_myinfo(request:Request) -> dict:
    content = {'나는 로그인을 원한다.':'아니 로그인 되는건가?'}

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

