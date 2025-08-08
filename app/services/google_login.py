# import hashlib

import google.oauth2.credentials
import google_auth_oauthlib.flow # 사용자 승인
from fastapi import Request, HTTPException
from starlette.responses import RedirectResponse


#### OAuth2.0 액세스 토큰 가져오기
# app이 Google OAuth2.0 서버와 상호작용, 사용자를 대신해 API 요청을 실행하기 위한 동의를 받음.
async def create_authorization_url():
    # 사용자 인증 정보를 만든 후, 다운 받은 client_secret.json 파일 정보를 사용, 애플리케이션 식별하는 flow 객체를 만든다.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=[  # 어떤 정보에 접근을 할 수 있는지 지정
            'https://www.googleapis.com/auth/userinfo.email',  # 기본 Google 계정 이메일 주소
            'https://www.googleapis.com/auth/userinfo.profile',  # 공개로 설정한 개인정보 전부 포함이 된 프로필
            'openid'  # google에서 내 개인 정보를 나와 연결, 사용자 정보와 연관된 고유한 식별자 ID 발급.
        ]
    )

    # 리디렉션할 위치 지정
    flow.redirect_uri = 'http://localhost:8000/auth/google/login/callback'
    # flow.redirect_uri = 'https://kimshineday.github.io/maroo-maroo-maroo/'
    # Google OAuth 2.0 서버 요청을 위한 URL 생성, kwargs 사용해 선택적 요청 매개변수 설정.
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # 엑세스 토큰을 새로 고칠 수 있다, access_token과 refresh_token 발급
        include_granted_scopes='true',  # 애플리케이션이 이미 사용자에게 특정 권한을 동의 받았지만, 추가적인 권한을 요청할 때 사용.
        prompt='consent'  # 사용자에게 동의를 요청
    )

    # CSRF 공격 방지 위해 state 값을 세션에 저장하는 로직 필요 ????

    return authorization_url


