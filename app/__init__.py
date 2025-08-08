from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from app.configs.tortoise_config import initialize_tortoise
from app.apis.google_login import router as google_login
app = FastAPI(default_response_class=ORJSONResponse)
initialize_tortoise(app=app)

app.include_router(google_login)