from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from app.configs.tortoise_config import initialize_tortoise

app = FastAPI(default_response_class=ORJSONResponse)
initialize_tortoise(app=app)