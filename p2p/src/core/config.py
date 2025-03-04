from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_title: str = 'CipherSwap'
    app_description: str = 'Описание проекта'
    secret: str = 'SECRET'
    DATABASE_URL: str
    TELEGRAM_BOT_TOKEN: str
    ADMIN_TOKEN: str
    TIMEZONE: Optional[str] = 'Europe/Moscow'
    FFIO_APIKEY: str
    FFIO_SECRET: str
    DOMAIN: str
    SECRET_KEY: str

    REDIS_HOST: Optional[str] = 'localhost'
    REDIS_PORT: Optional[str] = '6379'
    REDIS_DATABASE: Optional[int] = 0

    class Config:
        env_file = '.env'


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
