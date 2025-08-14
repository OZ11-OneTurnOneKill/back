import json
import httpx
import random
from app.dtos.users import User, GetMyInfo
from app.models.user import UserModel
from google.oauth2.credentials import Credentials


# profile data
# async def info(credentials: Credentials): # 구글API에 사용자 정보 요청
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             'https://www.googleapis.com/oauth2/v2/userinfo',
#             headers={'Authorization': f'Bearer {credentials.token}'}
#         )
#         # print('요청에 문제가 발생했습니다.')
#         response.raise_for_status() # 요청 실패할 경우, 예외 발생
#
#         user_info = response.json() # json으로 데이터 받아옴.
#
#         return user_info


async def get_info(user_id : int) -> GetMyInfo:
    info = await UserModel.get(id=user_id)
    print(GetMyInfo(
        id=info.id,
        nickname=info.nickname,  # Social Account
        profile_image_url=info.profile_image_url,  # Social Account
        email=info.email,
    ))
    return GetMyInfo(
        id = info.id,
        nickname = info.nickname, # Social Account
        profile_image_url = info.profile_image_url,  # Social Account
        email = info.email,
    )




async def get_or_create_user(user_info):
    # user_info는 구글에서 받은 유저 데이터 (dict)
    # social_account는 SocialAccountModel 인스턴스

    # 이메일이나 소셜계정 기준으로 유저 조회
    user = await UserModel.filter(email=user_info['email']).first()

    if not user: # 기존 데이터에 없을 경우, 새로운 유저 생성.
        base_nickname = '반가워요' # 기본 베이스 닉네임
        while True:
            random_suffix = random.randint(1000, 9999) # 랜덤으로 4자리 숫자를 출력, 기본 베이스 닉네임 뒤에 랜덤으로 생성된 숫자를 추가.
            create_nickname = f"{base_nickname}{random_suffix}"
            if not await UserModel.filter(nickname=create_nickname): # 유니크 설정 되어있는 닉네임, 중복 방지를 위한 DB 확인
                nickname = create_nickname # 없을 경우 닉네임으로 생성
                break

        user = await UserModel.create(
            provider='google',
            provider_id=user_info.get('id'),
            email=user_info.get('email'),
            nickname=nickname,
            profile_image_url=user_info.get('picture'),
            is_active=True,
            is_superuser=False,
        )
        print(f'새로운 유저 {user.nickname} 생성됨')
    else:
        print(f'기존 유저 {user.nickname} 가져옴')

    return user


"""async def get_google_user_data(credentials: Credentials):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        response.raise_for_status()
        return response.json()"""


async def save_google_userdata(credentials: Credentials):
    # 구글 유저 데이터 가져오기
    async with httpx.AsyncClient() as client:
        url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        response = await client.get(
            url,
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        response.raise_for_status()
        user_info = response.json()

        user = await get_or_create_user(user_info)


        # # 닉네임 랜덤 생성
        # base_nickname = '반가워요'
        # random_suffix = random.randint(1000, 9999)
        # nickname = f"{base_nickname}{random_suffix}"
        #
        #
        # # DB에 등록된 데이터와 비교
        # social_account, created = await UserModel.get_or_create( # social_account=조회할 데이터 / created=DB에 해당 데이터(레코드) 여부 조회. (True일때 데이터 등록, 기존에 데이터 있을 경우 False 출력)
        #     provider='google',
        #     provider_id=user_info['id'],
        #     email=user_info['email'],
        #     nickname=user_info['nickname'],
        #     profile_image_url=user_info['picture'],
        #     is_active=True,
        #     is_superuser=False,
        # )
        #
        # user = await get_or_create_user(user_info)
        #
        # if created == True:
        #     # 회원 정보 DB에 등록
        #     # new_google_user = await SocialAccount.create(
        #     #     provider='google',
        #     #     provider_id=user_info['id'],
        #     #     email=user_info['email']
        #     # )
        #     new_user = await UserModel.create(
        #         provider='google',
        #         provider_id=user_info['id'],
        #         email=user_info['email'],
        #         nickname=nickname,
        #         profile_image_url=user_info['picture'],
        #         is_active=True,
        #         is_superuser=False,
        #     )
        #     social_account.user = new_user # 테이블간의 관계성 부여
        #     await social_account.save() # DB 저장
        #     print(f'{new_user.nickname} 유저 데이터가 저장 되었습니다.')
        #
        # else:
        #     await UserModel.fetch_related(social_account)

