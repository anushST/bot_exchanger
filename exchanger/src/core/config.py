import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_STATE = os.getenv("ENV_STATE", "dev")

ENV_FILES = [
    "env/.env",
    f"env/.env.{ENV_STATE}"
]


class Settings(BaseSettings):
    app_title: str = 'CipherSwap'
    app_description: str = 'Описание проекта'
    secret: str = 'SECRET'
    DATABASE_URL: str
    TOKEN: str
    ADMIN_TOKEN: str
    EASYBIT_API_KEY: str
    TIMEZONE: Optional[str] = 'Europe/Moscow'
    FFIO_APIKEY: str
    FFIO_SECRET: str
    CHANGELLY_PRIVATE_KEY: str
    CHANGELLY_X_API_KEY: str
    DOMAIN: str

    REDIS_HOST: Optional[str] = 'localhost'
    REDIS_PORT: Optional[str] = '6379'
    REDIS_DATABASE: Optional[int] = 0

    model_config = SettingsConfigDict(env_file=ENV_FILES, extra="ignore")


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s|%(name)s|%(levelname)s|%(message)s|"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/backend.log",
            "formatter": "default",
            "level": "DEBUG"
        },
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
            "level": "INFO"
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn.error": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn.access": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file", "console"]
    }
}


settings = Settings()
