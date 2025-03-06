from aiogram import Bot

from .base import NotificationType
from src.core.config import settings
from src.models import User

bot = Bot(settings.TELEGRAM_BOT_TOKEN)


class TelegramNotification(NotificationType):
    async def send_message(self, user: User, message: str):
        """Отправляет сообщение пользователю через aiogram"""
        if not user.tg_id:
            return
        try:
            await bot.send_message(chat_id=user.tg_id, text=message)
        except Exception as e:
            raise Exception(f"Ошибка при отправке сообщения: {e}")
