"""
# app/services/users/kakao_login.py
kakao 소셜 로그인 구현 api service logic 관리 파일입니다.
소셜 로그인 관련 라우터는 `apis/` 폴더에 작성했습니다.

"""
from fastapi import HTTPException

import requests
from app.configs.base_config import Kakao
from fastapi import Request
from fastapi.responses import RedirectResponse
from typing import Optional

kakao = Kakao()


async def create_authorization_url(request:Request, scope: Optional[str]) -> RedirectResponse:
    """
    # 카카오 인증 서버로 인가 코드 발급 요청을 하기 위한 링크 생성.
    동의 항목을 키워드로 전달해서 접근 권한 요청을 한다.
    권한 요청 링크 생성 후, RedirectResponse.
    """
    # 링크 생성
    scope_param = f'&scope={scope}' if scope else '' # 동의항목 설정

    redirect_url = f'{kakao.KAUTH_HOST}/oauth/authorize?response_type=code&client_id={kakao.KAKAO_KEY}&redirect_uri={kakao.KAKAO_REDIRECT_URI}{scope_param}'
    print(f"""
    authorization_url : 
    {redirect_url}
    """)

    return RedirectResponse(redirect_url)


async def redirect_page(request: Request):
    """
    # 인가 코드 발급 및 access token 생성
    access_token 을 받아 세션에 저장.
    :return:
    """

    code = request.query_params.get('code')
    error = request.query_params.get('error')
    state = request.query_params.get('state')

    print('쿼리 파라미터: ', request.query_params)
    print(
        {
            'code': code,
            'error': error,
            'state': state,
        }
    )

    if error:
        return {'error': error, 'description': 'OAuth 인증에 실패 했습니다.'}
    if not code:
        return {'error': code, 'description': '발급 받은 인가 코드가 없습니다.'}

    # access token 발급 받을때 필요한 데이터
    data = {
        'grant_type': 'authorization_code',
        'client_id': kakao.KAKAO_KEY,
        'redirect_uri': kakao.KAKAO_REDIRECT_URI,
        'client_secret': kakao.KAKAO_CLIENT_ID,
        'code': code # 카카오에서 준 인가 코드
    }
    print(data)


    # access token 요청
    try:
        response = requests.post( # 카카오에 요청 시도
            f'{kakao.KAUTH_HOST}/oauth/token',
            data=data,
            # headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        print(f'kakao access token 요청 : {response.json()}')

        if response.status_code == 200: # access token 받아왔을 경우.
            token_info = response.json()
            print(f'kakao accesstoken: {token_info}')
            request.session['access_token'] = token_info
            check_session = request.session.get('access_token')
            print(f'session에 저장 되었나?: {check_session}')

            return check_session


    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error: {str(e)}')

async def get_userinfo(request: Request):
    """
    유저가 허용한 카카오에서 제공하는 유저 데이터를 받아온다.
    카카오에서 발급해준 access token를 헤더에 넣어 요청
    """

    token_info = request.session.get('access_token')

    headers = {  # Header에
        # 'Authorization': 'Bearer ' + request.session.get('access_token', '')
        'Authorization': f'Bearer {token_info["access_token"]}'
    }

    response = requests.get(kakao.KAPI_HOST + '/v2/user/me', headers=headers)

    return response.json()