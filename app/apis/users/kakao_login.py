"""
# app/apis/users/kakao_login.py
kakao 소셜 로그인 구현 api router 관리 파일입니다.
소셜 로그인 관련 로직은 `services/` 폴더에 작성했습니다.
"""

from fastapi import APIRouter,Depends


router = APIRouter(prefix='api/v1/users/auth/kakao', tags=['kakao'])

@router.post('/login')


@router.get('/login/callback')


@router.post('/logout')
