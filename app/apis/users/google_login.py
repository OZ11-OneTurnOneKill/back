"""
# app/apis/user/google_login.py
Google 소셜 로그인 구현 api router 관리 파일입니다.
소셜 로그인 관련 로직은 `services/` 폴더에 작성했습니다.
"""
from typing import Annotated

from fastapi import APIRouter, Request, Depends
from starlette.responses import RedirectResponse
from app.configs.base_config import Google
from app.models.user import RefreshTokenModel, UserModel
from app.services.users.google_login import create_authorization_url, access_token, info, revoke
from app.services.users import login
from app.services.users.users import get_current_user, get_or_create_user
from google.oauth2.credentials import Credentials


router = APIRouter(prefix="/api/v1/users/auth/google", tags=["Google"])
google = Google()

# OAuth2.0 액세스 토큰 가져오기
# app이 Google OAuth2.0 서버와 상호작용, 사용자를 대신해 API 요청을 실행하기 위한 동의를 받음.
@router.get("/login", description='authorization_url 생성') # 로그인 및 권한 동의 페이지 URL 생성
async def get_authorization_url(request:Request) -> RedirectResponse:
    """
    원활한 서비스 이용을 위해 회원가입과 로그인을 구글 소셜 계정으로 하기 위해 권한 동의 페이지 URL을 생성 및 리턴 받는다.
    : 유저가 `/login` 요청 시, 이 함수가 실행이 되며 google login 페이지로 연결이 된다.
        -> 유저는 연결된 페이지에서 이 서비스 이용을 위해 정보 제공 동의가 이뤄지고, 이후 callback을 통해 회원 가입 및 로그인이 진행이 된다.
    """
    authorization_url = await create_authorization_url(request)
    return RedirectResponse(authorization_url) # google 소셜 로그인 페이지로 이동

@router.get("/login/callback", name='callback') # 구글에게 로그인 관련 데이터를 받음
async def get_access_token(request: Request): # access token 교환
    """
    이전 단계(`/login`)에서 유저의 동의까지 마무리.
    이를 토대로 유저 데이터를 받기 위한 access token 발급 단계.
    원활한 서비스 이용을 위해 JWT 토큰 발급까지 이뤄진다.
    """
    credentials = await access_token(request) # 토큰 발급, 데이터들은 session에 저장 및 user data 저장
    print(f'콜백에서 받은 credentials : {credentials}')

    """
    # JWT TOKEN 발급
    JWT 토큰을 발급 받기 위해 세션에 저장된 데이터를 확인 후, 토큰 발급이 진행된다.
    """
    try: # 세션에 저장되어있는 데이터 유무 확인
        state = request.session['state']
        provider_id = request.session['provider_id']
        print('state 값', state)
        print('provider_id', provider_id)
    except KeyError:
        return {'error': 'Session을 찾지 못했습니다.'}

    provider_id = request.session.get('provider_id') # google 소셜 로그인 ID
    print(provider_id, type(provider_id))

    if not provider_id: # 데이터가 없을때.
        print(f'세션에서 provider_id 조회가 안됩니다. 로그인을 다시 요청합니다. : {provider_id}')
        return RedirectResponse('/api/v1/users/auth/google/login')

    user = await UserModel.filter(provider_id=provider_id).first() # 로그인한 유저의 데이터를 객체화
    print(f'user: {user.id}')

    jwt_access, expires = await login.create_access(str(user.id)) # jwt access token
    jwt_refresh, expires_at = await login.create_refresh(str(user.id)) # jwt refresh token
    print(f'access: {jwt_access}, refresh: {jwt_refresh}')

    await login.save_refresh(user, jwt_refresh, expires_at) # jwt refresh token 저장

    # token_data = {
    #     'access_token': jwt_access,
    # }
    # return token_data
    # url = f'{google.URL}+?token={jwt_access}'
    response = RedirectResponse(google.URL)
    response.set_cookie(
        key='access_token',
        value=jwt_access,
        httponly=True,
        secure=google.IS_SECURE,
        samesite=None,
        domain=google.DOMAIN) # 개발 서버 올릴때 secure = True 변경 필요

    return response

@router.post('/logout')
# @router.get('/logout') # 로그아웃 테스트 확인용 get 라우터, front 연결 시 삭제
async def post_revoke(request: Request, current_user: Annotated[UserModel, Depends(get_current_user)]) -> RedirectResponse:
    """
    유저가 로그아웃 요청시, 로그아웃 관련 로직들이 실행.
    response(revoke) : 세션 삭제 및 쿠키 삭제 후 지정한 url로 이동
    """
    print('라우터에서의 함수 실행 완')
    response = await revoke(request, current_user)
    print('토큰 삭제 함수 실행 완')
    # return RedirectResponse(url='/')
    # return '라우터 문제는 아닌가봐.'
    return response

"""@router.get('/myinfo')
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

"""
