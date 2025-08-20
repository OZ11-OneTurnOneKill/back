"""
# app/apis/users/kakao_login.py
kakao 소셜 로그인 구현 api router 관리 파일입니다.
소셜 로그인 관련 로직은 `services/` 폴더에 작성했습니다.
"""
from app.services.users.users import get_or_create_kakao
from app.services.users.kakao_login import create_authorization_url, redirect_page, get_userinfo
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from typing import Optional


router = APIRouter(prefix='/api/v1/users/auth/kakao', tags=['kakao'])


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
    # kakao access token 발급 > session에 저장
    kakao_access = await redirect_page(request)
    print(f'카카오에서 준 access token : {kakao_access}')

    # 로그인한 유저 데이터를 가져옴
    user_info = await get_userinfo(request)
    print(f'user 정보 : {user_info}')

    # 유저 데이터 저장 및 조회
    # 신규 유저일 경우 조회 후 저장, 기존 유저일 경우 조회.
    await get_or_create_kakao(user_info)

    return '일단 로그인인 된듯?!'


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
# @router.post('/logout')
