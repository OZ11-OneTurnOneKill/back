# DTO, 데이터 유효성 검사
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional
from datetime import datetime

class ProviderType(str, Enum):
    GOOGLE = "google"
    KAKAO = "kakao"

class User(BaseModel):
    social_account : int # SocialAccountModel FK
    # social_account : SocialAccountModel
    nickname : str = Field(..., min_length=1, max_length=8) # 닉네임 : 8글자 제한
    profile_image_url : Optional[str] = None # 프로필 이미지 : 기본 값으로 None 설정
    is_active : bool = True # 사용자 계정 활성화 여부 : 필드 생략 시, True 설정
    is_superuser : bool = False # 관리자 계정 여부 : 필드 생략 시, False 설정

class SocialAccount(BaseModel):
    provider : ProviderType # 소셜 로그인 종류 : Enum으로 데이터 값을 받음 (google, kakao)
    provider_id : str # 소셜 로그인 아이디
    email : EmailStr # 이메일


# 토큰
class TokenUserData(BaseModel):
    user : int

class Token(BaseModel):
    access_token : str
    token_type : str

class RefreshToken(BaseModel):
    user : int # usermodel FK
    token : str
    # access_token : str
    # refresh_token : str
    expires_at : datetime
    revoked : bool # 토큰 취소 여부 -> 로그아웃 여부 : 로그아웃 시 True로 변경

# myinfo 페이지에 출력될 데이터
class GetMyInfo(BaseModel):
    id : int
    nickname :str # Social Account
    profile_image_url : str # Social Account
    email : EmailStr # User

# 닉네임 수정
class PatchNickname(BaseModel):
    nickname : str = Field(min_length=1, max_length=8) # 닉네임
