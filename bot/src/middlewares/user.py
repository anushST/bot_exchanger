from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.future import select

from src.models.user import User


class UserMiddleware(BaseMiddleware):

    async def __call__(self, handler, event: TelegramObject, data: dict):
        session = data["session"]
        result = await session.execute(select(User).filter_by(tg_id=event.from_user.id))
        user = result.scalars().first()
        if not user:
            user = User(
                tg_id=event.from_user.id,
                tg_name=event.from_user.full_name,
                tg_username=event.from_user.username or ""
            )
            session.add(user)
            await session.commit()

        data["user"] = user
        data["lang"] = user.get_lang()
        return await handler(event, data)
