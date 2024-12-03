from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class DataBaseMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        super().__init__()
        self.session_factory = session_factory

    async def __call__(self, handler, event: TelegramObject, data: dict):
        with self.session_factory() as session:
            try:
                data["session"] = session
                return await handler(event, data)
            finally:
                session.commit()
