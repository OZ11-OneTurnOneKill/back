from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from app.configs.tortoise_config import initialize_tortoise
from app.apis.community.study_router import router as study_router
from app.apis.community.free_router import router as free_router
from app.apis.community.share_router import router as share_router
from app.apis.community.common_router import router as common_router
from app.apis.ai_study_plan.ai_study_plan_router import router as ai_study_plan_router


tags_metadata = [
    {"name": "Community · Study", "description": "스터디 모집 게시글 API"},
    {"name": "Community · Free",  "description": "자유 게시판 API"},
    {"name": "Community · Share", "description": "자료 공유 게시글 API"},
    {"name": "Community · Common","description": "댓글, 좋아요, 삭제 등 공통 API"},
    {"name": "AI Study Plan", "description": "AI 학습 계획 API"},
]

app = FastAPI(default_response_class=ORJSONResponse, openapi_tags=tags_metadata)

app.include_router(study_router)
app.include_router(free_router)
app.include_router(share_router)
app.include_router(common_router)
app.include_router(ai_study_plan_router)

initialize_tortoise(app=app)