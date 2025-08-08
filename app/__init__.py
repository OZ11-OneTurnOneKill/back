from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from app.configs.tortoise_config import initialize_tortoise
from app.apis.ai_study_plan_router import router as study_plan_router

app = FastAPI(default_response_class=ORJSONResponse)
app.include_router(study_plan_router)
initialize_tortoise(app=app)