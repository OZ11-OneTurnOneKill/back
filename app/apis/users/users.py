import json
from app.services.users.users import info
from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse
from google.oauth2.credentials import Credentials

router = APIRouter(prefix='/api/v1/users')

@router.get('/myinfo')
async def get_myinfo(request:Request) -> dict:
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

