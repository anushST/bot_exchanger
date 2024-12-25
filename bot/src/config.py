from typing import Optional

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    DATABASE_URL: str
    TOKEN: str
    TIMEZONE: Optional[str] = 'Europe/Moscow'
    FFIO_APIKEY: str
    FFIO_SECRET: str

    REDIS_HOST: Optional[str] = 'localhost'
    REDIS_PORT: Optional[str] = '6379'
    REDIS_DATABASE: Optional[int] = 0

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Config()


class KeyboardCallbackData:
    START = "start"
    CANCEL = "cancel"
    CHANGE_LANGUAGE = "change_lang"
    SET_LANGUAGE = "set_lang_"

    EXCHANGE_CREATE = "exchange_create"
    EXCHANGE_CONFIRM = "exchange_confirm"
    EXCHANGE_FIX_RATE = "exchange_fix_rate"
    EXCHANGE_FLOAT_RATE = "exchange_float_rate"

    EMERGENCY_EXCHANGE = 'emergency_exchange:'  # after goes transaction id
    EMERGENCY_REFUND = 'emergency_refund:'  # after goes transaction id

    FAQ = "faq"
    FAQ_QUESTION = "faq_question_"

    @staticmethod
    def get_faq_question(question_id):
        return KeyboardCallbackData.FAQ_QUESTION + str(question_id)
