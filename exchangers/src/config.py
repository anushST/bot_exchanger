from typing import Optional

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    DATABASE_URL: str
    FFIO_APIKEY: str
    FFIO_SECRET: str
    EASYBIT_API_KEY: str
    ADMIN_TOKEN: str
    DOMAIN: str
    TOKEN: str

    REDIS_HOST: Optional[str] = 'localhost'
    REDIS_PORT: Optional[str] = '6379'
    REDIS_DATABASE: Optional[int] = 0

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Config()
