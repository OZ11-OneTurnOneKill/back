from enum import StrEnum

from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class Env(StrEnum):
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"

load_dotenv()

class Config(BaseSettings):
    ENV: Env = Env.LOCAL

    DB_HOST: str = "DB_HOST"
    DB_PORT: int = "DB_PORT"
    DB_USER: str = "DB_USER"
    DB_PASSWORD: str = "DB_PASSWORD"
    DB_NAME: str = "DB_NAME"