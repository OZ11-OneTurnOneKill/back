from typing import Annotated

from fastapi import APIRouter, Request
from fastapi.params import Depends
from starlette.responses import RedirectResponse
from app.configs.base_config import Google
from app.models.user import RefreshTokenModel, UserModel
from app.services.users.google_login import create_authorization_url, access_token, info, revoke
from app.services.users import login
from app.services.users.users import save_google_userdata, get_current_user
from google.oauth2.credentials import Credentials


router = APIRouter(prefix="/api/v1/users/auth/google", tags=["Google"])
google = Google()


# OAuth2.0 액세스 토큰 가져오기
# app이 Google OAuth2.0 서버와 상호작용, 사용자를 대신해 API 요청을 실행하기 위한 동의를 받음.
# @router.post("auth/google/login")
# async def google_login_post()
@router.get("/login", description='authorization_url 생성') # 로그인 및 권한 동의 페이지 URL 생성
async def get_authorization_url(request:Request) -> RedirectResponse:
    authorization_url = await create_authorization_url(request)
    return RedirectResponse(authorization_url)

@router.get("/login/callback", name='callback') # 구글에게 로그인 관련 데이터를 받음
async def get_access_token(request: Request) -> RedirectResponse: # access token 교환
    credentials = await access_token(request)
    print(f'콜백에서 받은 credentials : {credentials}')
    # features = check_granted_scopes(credentials)

    # JWT TOKEN 발급
    # social_account = await save_google_userdata(credentials) # 가입 정보 (혹은 로그인 정보)를 DB에서 가져옴.
    # print(f'social_accounts: {social_account}', type(social_account))

    try:
        state = request.session['state']
        provider_id = request.session['provider_id']
        print('state 값', state)
        print('provider_id', provider_id)
    except KeyError:
        return {'error': 'Session을 찾지 못했습니다.'}

    provider_id = request.session.get('provider_id')
    print(provider_id, type(provider_id))
    if not provider_id:
        print(f'세션에서 provider_id 조회가 안됩니다. 로그인을 다시 요청합니다. : {provider_id}')
        return RedirectResponse('/api/v1/users/auth/google/login')

    user = await UserModel.filter(provider_id=provider_id).first() # 로그인한 유저의 데이터를 객체화
    print(f'user: {user.id}')

    jwt_access, expires = await login.create_access(str(user.id)) # jwt access token
    jwt_refresh, expires_at = await login.create_refresh(str(user.id)) # jwt refresh token
    print(f'access: {jwt_access}, refresh: {jwt_refresh}')

    await login.save_refresh(user, jwt_refresh, expires_at) # jwt refresh token 저장

    response = RedirectResponse(google.URL)
    response.set_cookie(key='access_token', value=jwt_access, httponly=True, secure=False) # 개발 서버 올릴때 secure = True 변경 필요

    return response

@router.post('/logout')
# @router.get('/logout') # 로그아웃 테스트 확인용 get 라우터, front 연결 시 삭제
async def post_revoke(request: Request, current_user: Annotated[UserModel, Depends(get_current_user)]) -> RedirectResponse:
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