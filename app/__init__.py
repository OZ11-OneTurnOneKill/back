import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=False)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.middleware.sessions import SessionMiddleware
from app.configs.tortoise_config import initialize_tortoise
from app.configs.base_config import Google
# community
from app.apis.community.study_router import router as study_router
from app.apis.community.free_router import router as free_router
from app.apis.community.share_router import router as share_router
from app.apis.community.common_router import router as common_router
from app.apis.community.post_router import router as post_router
from app.apis.community.notification_ws_router import router as ws_router
from app.apis.community.top5_router import router as top_router
from app.apis.ai_router.ai_study_plan_router import router as ai_study_plan_router
from app.apis.ai_router.ai_summary_router import router as ai_summary_router
# user
from app.apis.users.users import router as users_router
from app.apis.users.google_login import router as google_login


tags_metadata = [
    {"name": "Community · Study", "description": "스터디 모집 게시글 API"},
    {"name": "Community · Free",  "description": "자유 게시판 API"},
    {"name": "Community · Share", "description": "자료 공유 게시글 API"},
    {"name": "Community · Common", "description": "댓글, 좋아요, 삭제 등 공통 API"},
    {"name": "Community · Post", "description": "각 게시글 전체 조회 API"},
    {"name": "Community · Top", "description": "각 커뮤니티 Top5 조회 API"},
    {"name": "AI Study Plan", "description": "AI 학습 계획 API"},
    {"name": "AI Summary", "description": "AI 정보 요약 API"},
    {"name": "Google", "description": "Google 소셜 로그인 API"},
    {"name": "Users", "description": "Users API"},
]

app = FastAPI(default_response_class=ORJSONResponse, openapi_tags=tags_metadata)

# community
app.include_router(post_router)
app.include_router(study_router)
app.include_router(free_router)
app.include_router(share_router)
app.include_router(common_router)
app.include_router(ws_router)
app.include_router(top_router)
app.include_router(ai_study_plan_router)
app.include_router(ai_summary_router)
# user
app.include_router(google_login)
app.include_router(users_router)

# 체크후 삭제
# load_dotenv()
# secret_key = os.getenv('SECRET_KEY')

google = Google()

origins = [
    "http://localhost:8000",
    "https://www.evida.site",
    "https://backend.evida.site",
    "https://eunbin.evida.site",
]
app.add_middleware(
    SessionMiddleware,
    secret_key=google.SECRET_KEY,

)
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