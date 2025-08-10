import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.middleware.sessions import SessionMiddleware
from app.configs.tortoise_config import initialize_tortoise
from app.apis.community_router import router as community_router
from app.apis.start import router as star_router
from app.apis.google_login import router as google_login
from app.apis.community_router import router as community_router
from app.apis.google_login import router as google_login

load_dotenv()
secret_key = os.getenv('SECRET_KEY')
app = FastAPI(default_response_class=ORJSONResponse)
app.include_router(community_router)
app.include_router(google_login)
app.include_router(star_router)
app.include_router(community_router)


origins = [
    # "http://localhost:8000", # 개발용 서버
    "https://www.evida.site"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # API를 호출할 수 있는 도메인을 지정.
    allow_credentials=True, # 자격증명(쿠키, http 인증) 허용 여부
    allow_methods=["*"], # 허용할 http 메소드
    allow_headers=["*"], # 허용할 http 헤더
)

router = APIRouter()
@router.get('/')
async def root():
    return {'시작해볼까':'좋지'}

app.add_middleware(SessionMiddleware, secret_key=secret_key)

initialize_tortoise(app=app)