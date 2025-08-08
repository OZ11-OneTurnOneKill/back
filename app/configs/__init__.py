from app.configs.base_config import Config


def get_config() -> Config:
    return Config()


config = get_config()