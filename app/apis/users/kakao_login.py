"""
# app/apis/users/kakao_login.py
kakao 소셜 로그인 구현 api router 관리 파일입니다.
소셜 로그인 관련 로직은 `services/` 폴더에 작성했습니다.
"""

from app.configs.base_config import Google
from app.models.user import UserModel
from app.services.users import login
from app.services.users.users import get_or_create_kakao, get_current_user
from app.services.users.kakao_login import create_authorization_url, redirect_page, get_userinfo, revoke
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from typing import Optional, Annotated




router = APIRouter(prefix='/api/v1/users/auth/kakao', tags=['Kakao'])
kakao_ = Google()


@router.get('/login')
async def login_kakao(request: Request) -> RedirectResponse:
    """
    카카오 로그인 페이지를 불러옵니다.
    :return: 카카오 로그인 url RedirectResponse
    """
    response = await create_authorization_url(request, scope='')
    return response
    # return RedirectResponse(url='http://localhost:8000/api/v1/users/auth/kakao/login/callback')

@router.get('/login/callback')
async def call_back(request: Request):
    """
    인가코드를 통해 유저 데이터를 받을 수 있는 access token을 발급,
    유저 데이터를 가져와 저장 및 jwt token을 생성한다.
    """
    ## kakao access token 발급 > session에 저장
    kakao_access = await redirect_page(request)
    print(f'카카오에서 준 access token : {kakao_access}')

    ## 로그인한 유저 데이터를 가져옴
    user_info = await get_userinfo(request)
    print(f'user 정보 : {user_info}')

    ## 유저 데이터 저장 및 조회
    # 신규 유저일 경우 조회 후 저장, 기존 유저일 경우 조회.
    user = await get_or_create_kakao(user_info)

    ## JWT token 발급
    jwt_access, expires = await login.create_access(str(user.id))  # jwt access token
    jwt_refresh, expires_at = await login.create_refresh(str(user.id))  # jwt refresh token
    print(f'access: {jwt_access}, refresh: {jwt_refresh}')

    await login.save_refresh(user, jwt_refresh, expires_at)  # jwt refresh token 저장

    response = RedirectResponse(kakao_.URL)
    response.set_cookie(
        key='access_token',
        value=jwt_access,
        httponly=True,
        secure=kakao_.IS_SECURE,
        samesite=None,
        domain=kakao_.DOMAIN)  # 개발 서버 올릴때 secure = True 변경 필요

    return response


@router.get('/profileimg')
async def get_profile_img(request: Request):
    """
    카카오 유저 프로필 이미지 가져오지 못하는 문제를 해결하기 위한 테스트 router
    """
    user = await get_userinfo(request) # 유저데이터 가져오기
    print(user)
    # user_img = user['properties']['profile_image']
    user_img = user.get('properties').get('profile_image')
    return user_img


@router.post('/logout')
async def logout_kakao(request: Request, current_user: Annotated[UserModel, Depends(get_current_user)]):
    """
    유저가 로그아웃 요청시, 로그아웃 관련 로직들이 실행.
    response(revoke) : 세션 삭제 및 쿠키 삭제 후 지정한 url로 이동
    """
    print('라우터에서의 함수 실행 완')
    # 카카오 로그아웃 API 실행
    response = await revoke(request, current_user)
    print('토큰 삭제 함수 실행 완')

    # return RedirectResponse(url='/')
    # return '라우터 문제는 아닌가봐.'
    return response