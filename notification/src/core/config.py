import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_STATE = os.getenv("ENV_STATE", "dev")

ENV_FILES = [
    "env/.env",
    f"env/.env.{ENV_STATE}"
]


class Settings(BaseSettings):
    DATABASE_URL: str
    DOMAIN: str

    TELEGRAM_BOT_TOKEN: str

    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_EMAIL: str
    SMTP_EMAIL_PASSWORD: str

    KAFKA_BOOTSTRAP_SERVICE: str = 'kafka:9092'

    REDIS_HOST: Optional[str] = 'redis'
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
            "filename": "logs/notification.log",
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
