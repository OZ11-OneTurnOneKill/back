from fastapi import APIRouter
from google.auth.transport.urllib3 import Request
from starlette.responses import RedirectResponse

from app.dtos import users
from app.dtos.users import SocialAccountModel
from app.models import user
from app.services.google_login import create_authorization_url, access_token

router = APIRouter(prefix="auth/google/login")


# OAuth2.0 액세스 토큰 가져오기
# app이 Google OAuth2.0 서버와 상호작용, 사용자를 대신해 API 요청을 실행하기 위한 동의를 받음.
# @router.post("auth/google/login")
# async def google_login_post()
@router.get("/", description='authorization_url 생성') # 로그인 및 권한 동의 페이지 URL 생성
async def get_authorization_url() -> RedirectResponse:
    authorization_url = await create_authorization_url()
    return RedirectResponse(authorization_url)