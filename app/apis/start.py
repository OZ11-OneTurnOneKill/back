from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, APIRouter

app = FastAPI()

# 도메인 설정
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