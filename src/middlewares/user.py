from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.models.user import User


class UserMiddleware(BaseMiddleware):

    async def __call__(self, handler, event: TelegramObject, data: dict):
        session = data["session"]
        user = session.query(User).filter_by(tg_id=event.from_user.id).first()
        if not user:
            user = User(
                tg_id=event.from_user.id,
                tg_name=event.from_user.full_name,
                tg_username=event.from_user.username or ""
            )
            session.add(user)
            session.commit()

        data["user"] = user
        data["lang"] = user.get_lang()
        return await handler(event, data)
