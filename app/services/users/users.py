import httpx
from google.oauth2.credentials import Credentials


# profile data
async def info(credentials: Credentials): # 구글API에 사용자 정보 요청
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        print('요청에 문제가 발생했습니다.')
        response.raise_for_status() # 요청 실패할 경우, 예외 발생

        user_info = response.json() # json으로 데이터 받아옴.

        return user_info