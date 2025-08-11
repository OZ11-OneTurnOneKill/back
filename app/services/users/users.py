import httpx
import random
from app.dtos.users import SocialAccount, User
from app.models.user import SocialAccountModel, UserModel
from google.oauth2.credentials import Credentials


# profile data
async def info(credentials: Credentials): # 구글API에 사용자 정보 요청
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        # print('요청에 문제가 발생했습니다.')
        response.raise_for_status() # 요청 실패할 경우, 예외 발생

        user_info = response.json() # json으로 데이터 받아옴.

        return user_info





async def get_or_create_user(user_info, social_account):
    # user_info는 구글에서 받은 유저 데이터 (dict)
    # social_account는 SocialAccountModel 인스턴스

    # 이메일이나 소셜계정 기준으로 유저 조회 (필요한 조건으로 변경 가능)
    user = await UserModel.filter(social_account=social_account).first()

    base_nickname = user_info.get('name') or "user"
    random_suffix = random.randint(1000, 9999)
    nickname = f"{base_nickname}_{random_suffix}"

    if not user:
        user = await UserModel.create(
            nickname=nickname,
            profile_image_url=user_info.get('picture'),
            social_account=social_account,
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
    async with httpx.AsyncClient() as client:
        url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        response = await client.get(
            url,
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        response.raise_for_status()
        user_info = response.json()

        # DB에 등록된 데이터와 비교
        social_account, created = await SocialAccountModel.get_or_create( # social_account=조회할 데이터 / created=DB에 해당 데이터(레코드) 여부 조회. (True일때 데이터 등록, 기존에 데이터 있을 경우 False 출력)
            provider='google',
            provider_id=user_info['id'],
            email=user_info['email']
        )

        user = await get_or_create_user(user_info, social_account)

        base_nickname = user_info.get('name') or "user"
        random_suffix = random.randint(1000, 9999)
        nickname = f"{base_nickname}_{random_suffix}"

        if created == True:
            # 회원 정보 DB에 등록
            # new_google_user = await SocialAccount.create(
            #     provider='google',
            #     provider_id=user_info['id'],
            #     email=user_info['email']
            # )
            new_user = await UserModel.create(
                social_account=social_account,
                nickname=nickname,
                profile_image_url=user_info['picture'],
                is_active=True,
                is_superuser=False,
            )
            social_account.user = new_user # 테이블간의 관계성 부여
            await social_account.save() # DB 저장
            print(f'{new_user.nickname} 유저 데이터가 저장 되었습니다.')

        else:
            await UserModel.fetch_related(social_account)

