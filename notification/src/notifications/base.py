from abc import ABC, abstractmethod

from src.models import User


class NotificationType(ABC):
    """Абстрактный класс, требующий реализации метода send_message"""

    @abstractmethod
    async def send_message(self, user: User, message: str):
        """Метод для отправки сообщения пользователю"""
        pass
