import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.middleware.sessions import SessionMiddleware
from app.configs.tortoise_config import initialize_tortoise
from app.apis.community_router import router as community_router
from app.apis.users.users import router as users_router
from app.apis.users.google_login import router as google_login
from app.apis.community_router import router as community_router

load_dotenv()
secret_key = os.getenv('SECRET_KEY')
app = FastAPI(default_response_class=ORJSONResponse)
app.include_router(community_router)
app.include_router(google_login)
app.include_router(users_router)
app.include_router(community_router)


origins = [
    # "http://localhost:8000", # 개발용 서버
    "https://www.evida.site"
]
app.add_middleware(SessionMiddleware, secret_key=secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # API를 호출할 수 있는 도메인을 지정.
    allow_credentials=True, # 자격증명(쿠키, http 인증) 허용 여부
    allow_methods=["*"], # 허용할 http 메소드
    allow_headers=["*"], # 허용할 http 헤더
)
"""
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # 인증 없이 접속 가능한 경로 설정
    public_paths = [
        '/', '/docs', '/openapi.json', # fastapi
        '/api/v1/users/auth/google/login', # 구글 소셜 로그인
        '/api/v1/users/auth/google/login/callback',
    ]

    if request.url.path in public_paths: # 요청 url과 public paths 비교
        return await call_next(request)
    # 로그인 확인
    token = request.session.get('token')
    if not token:
        print('미들웨어에서 토큰 조회 안됨')
        return RedirectResponse(url='/') # 아니 이거 어디로 보내야하나..?
    return await call_next(request) # fastapi에서 가지고 있는 함수
"""
router = APIRouter()

@router.get('/')
async def root():
    return {'시작해볼까':'좋지'}

app.include_router(router)

initialize_tortoise(app=app)