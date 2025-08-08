from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from app.configs.tortoise_config import initialize_tortoise
from app.apis.community_router import router as community_router

app = FastAPI(default_response_class=ORJSONResponse)
app.include_router(community_router)

initialize_tortoise(app=app)