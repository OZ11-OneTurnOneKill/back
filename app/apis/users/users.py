import json

from docutils.nodes import status
from app.configs.base_config import Google
from app.dtos.users import PatchNickname
from app.models.user import UserModel
from app.services.users.users import get_current_user, update_user
from app.services.users.login import user_check
from fastapi import APIRouter, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, RedirectResponse
from google.oauth2.credentials import Credentials


router = APIRouter(prefix='/api/v1/users', tags=['Users'])

security = HTTPBearer() # 토큰 헤더 받아옴
google = Google()


@router.get('/myinfo')
async def get_myinfo(user = Depends(get_current_user)):
    """
    유저 정보를 조회하는 라우터.
    """
    return {'id': user.id, 'nickname': user.nickname, 'email': user.email}


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
@router.patch('/myinfo')
async def patch_nickname(patch_nickname: PatchNickname, user = Depends(get_current_user)):
    """
    처음 가입할때 랜덤으로 생성된 닉네임을 유저가 원하는 닉네임으로 변경할 수 있다.
    :user: 로그인한 유저 데이터
    :patch_nickname: 변경하고자 하는 닉네임
    """
    updated_nickname = await update_user(user, patch_nickname.nickname) # 닉네임 변경 함수 실행
    print(updated_nickname, ' !!!!변경완료!!!!')

    return {
        'user_id' : user.id,
        'new_nickname' : updated_nickname,
        'msg' : '닉네임 변경이 완료 되었습니다.'
    }