from aiogram.filters import Filter
from aiogram.types import Message

from src.lang import Language


class MultilanguageTextFilter(Filter):

    def __init__(self, lang_path):
        self.lang_path = lang_path

    async def __call__(self, message: Message, **data) -> bool:
        self.expected_text = data['lang'].get(self.lang_path)
        return message.text == self.expected_text
