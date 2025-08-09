from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from app.configs.tortoise_config import initialize_tortoise
from app.apis.start import router as star_router
from app.apis.google_login import router as google_login
from app.apis.community_router import router as community_router
from app.apis.google_login import router as google_login

app = FastAPI(default_response_class=ORJSONResponse)
app.include_router(community_router)
app.include_router(google_login)
app.include_router(star_router)

initialize_tortoise(app=app)

