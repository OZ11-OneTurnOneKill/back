import asyncio
import httpx
import os
import json
from concurrent.futures.thread import ThreadPoolExecutor
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow # 사용자 승인
from fastapi import Request, HTTPException
from starlette.responses import RedirectResponse


load_dotenv()

client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
client_id = os.getenv('GOOGLE_CLIENT_ID')
redirect_uri = os.getenv('GOOGLE_REDIRECT_URIS')
auth_uri = os.getenv('GOOGLE_AUTH_URI')
token_uri = os.getenv('GOOGLE_TOKEN_URI')

client_config = {
    'web': {
        'client_id': client_id,
        'client_secret': client_secret,
        'auth_uri': auth_uri,
        'token_uri': token_uri,
        'redirect_uri': [redirect_uri],
    }
}

#### OAuth2.0 액세스 토큰 가져오기
# app이 Google OAuth2.0 서버와 상호작용, 사용자를 대신해 API 요청을 실행하기 위한 동의를 받음.
async def create_authorization_url(request: Request):
    # 사용자 인증 정보를 만든 후, 다운 받은 client_secret.json 파일 정보를 사용, 애플리케이션 식별하는 flow 객체를 만든다.
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=[  # 어떤 정보에 접근을 할 수 있는지 지정
            'https://www.googleapis.com/auth/userinfo.email',  # 기본 Google 계정 이메일 주소
            'https://www.googleapis.com/auth/userinfo.profile',  # 공개로 설정한 개인정보 전부 포함이 된 프로필
            'openid'  # google에서 내 개인 정보를 나와 연결, 사용자 정보와 연관된 고유한 식별자 ID 발급.
        ]
    )

    # 리디렉션할 위치 지정
    flow.redirect_uri = 'https://www.evida.site/api/v1/users/auth/google/login/callback' # 개발서버

    # Google OAuth 2.0 서버 요청을 위한 URL 생성, kwargs 사용해 선택적 요청 매개변수 설정.
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # 엑세스 토큰을 새로 고칠 수 있다, access_token과 refresh_token 발급
        include_granted_scopes='true',  # 애플리케이션이 이미 사용자에게 특정 권한을 동의 받았지만, 추가적인 권한을 요청할 때 사용.
        prompt='consent'  # 사용자에게 동의를 요청
    )

    request.session['state'] = state

    # CSRF 공격 방지 위해 state 값을 세션에 저장하는 로직 필요 ????

    return authorization_url

# state 기능이 있다..? 라이브러리에...?,
#   -> google_auth_oauthlib에 기본적으로 가지고 있다고 함.


def fetch_token(flow: Flow, authorization_response:str): # 동기 함수 분리
    # flow.fetch_token 메서드 사용, 해당 응답의 승인코드를 토큰으로 교환
    flow.fetch_token(authorization_response=authorization_response) # 함수 호출 (동기식)
    return flow.credentials

# access token 교환
async def access_token(request: Request):
    # 승인 서버 응답 확인
    try:
        state = request.session['state']
    except KeyError:
        return {'error': 'Session을 찾지 못했습니다.'}

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=[  # 어떤 정보에 접근을 할 수 있는지 지정
            'https://www.googleapis.com/auth/userinfo.email',  # 기본 Google 계정 이메일 주소
            'https://www.googleapis.com/auth/userinfo.profile',  # 공개로 설정한 개인정보 전부 포함이 된 프로필
            'openid'  # google에서 내 개인 정보를 나와 연결, 사용자 정보와 연관된 고유한 식별자 ID 발급.
        ],
        state=state, # flow에 client_secrets 파일과 scopes와 state를 담아 전달.
        redirect_uri='https://www.evida.site/api/v1/users/auth/google/login/callback'
    )
    flow.redirect_uri = request.url_for('callback') # 동적으로 리다이렉트할 url 생성, 구글에게 이 주소로 결과를 보내달라고 요청
    authorization_response = str(request.url) # 인증 코드를 보냄

    # 동기 함수를 비동기로 호출 (ThreadPoolExecutor 사용)
    executor = ThreadPoolExecutor()
    credentials = await asyncio.get_running_loop().run_in_executor(executor, fetch_token, flow, authorization_response)
    print(f'생성된 credentials : {credentials}')
    request.session['credentials'] = credentials.to_json()
    print(f'세션에 무사히 저장 완료')
    return credentials


    # 사용자가 부여한 권한 확인하기.
async def check_granted_scopes(credentials):
    features = {}
    if 'https://www.googleapis.com/auth/userinfo.email' in credentials['granted_scopes']:
        features['email'] = True
    else:
        features['email'] = False
    if 'https://www.googleapis.com/auth/userinfo.profile' in credentials['granted_scopes']:
        features['profile'] = True
    else:
        features['profile'] = False

# credentials = await check_granted_scopes(credentials)
    # return features
    return features

# profile data
async def info(credentials: Credentials): # 구글API에 사용자 정보 요청
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        response.raise_for_status() # 요청 실패할 경우, 예외 발생

        user_info = response.json() # json으로 데이터 받아옴.

        return user_info


async def revoke(request: Request):
    if 'credentials' not in request.session: # 세션에 저장된 데이터가 없을 경우
        print('세션 데이터 일치하지 않습니다. 확인 필요.')
        return RedirectResponse(url='/')

    credentials = Credentials.from_authorized_user_info(
        json.loads(request.session.get('credentials'))
    ) # 세션에서 데이터를 가져옴.

    # 비동기 HTTP 클라이언트인 httpx를 사용
    async with httpx.AsyncClient() as client:
        revoke_response = await client.post(
            'https://oauth2.googleapis.com/revoke',
            params={'token': credentials.token},
            headers={'content-type': 'application/x-www-form-urlencoded'}
        )

    # 응답 상태 코드로 성공/실패 여부 판단
    if revoke_response.status_code == 200:
        # 로그아웃 성공 시 세션 데이터 삭제
        del request.session['credentials']
        # 성공 메시지 반환 또는 홈으로 리디렉션
        print('로그아웃은 되었는데 여기선 확인을 못하는듯...')
        return RedirectResponse(url='/') # 로그아웃 성공 시 루트 페이지로 이동.
    else:
        # 로그아웃 실패 시 오류 메시지 반환
        return '로그아웃에 문제가 생겼습니다.'
