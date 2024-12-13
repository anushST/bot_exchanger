from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

import logging

logger = logging.getLogger(__name__)


class DataBaseMiddleware(BaseMiddleware):
    def __init__(self, async_session_factory):
        super().__init__()
        self.async_session_factory = async_session_factory

    async def __call__(self, handler, event: TelegramObject, data: dict):
        async with self.async_session_factory() as session:
            try:
                data["session"] = session
                return await handler(event, data)
            finally:
                await session.commit()
