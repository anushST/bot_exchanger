from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_title: str = 'CipherSwap'
    app_description: str = 'Описание проекта'
    secret: str = 'SECRET'
    DATABASE_URL: str
    TOKEN: str
    ADMIN_TOKEN: str
    TIMEZONE: Optional[str] = 'Europe/Moscow'
    FFIO_APIKEY: str
    FFIO_SECRET: str
    DOMAIN: str

    REDIS_HOST: Optional[str] = 'localhost'
    REDIS_PORT: Optional[str] = '6379'
    REDIS_DATABASE: Optional[int] = 0

    class Config:
        env_file = '.env'


settings = Settings()
