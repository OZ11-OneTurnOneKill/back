from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(StrEnum):
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")
    ENV: Env = Env.LOCAL

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "1234"
    DB_NAME: str = "study_with_ai"

class Google(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    GOOGLE_CLIENT_SECRET: str = 'client_secret'
    GOOGLE_CLIENT_ID: str = 'client_id'
    GOOGLE_REDIRECT_URIS: str = 'redirect_uris'
    GOOGLE_AUTH_URI: str = 'https://accounts.google.com/o/oauth2/auth'
    GOOGLE_TOKEN_URI: str = 'https://accounts.google.com/o/oauth2/token'

    REDIRECT_URI: str = 'uri'
    URL: str = 'url'

    SECRET_KEY: str = 'secret'


class Tokens(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1

