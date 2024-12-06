from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from src.lang import Language
from src.models.user import User
from src.config import KeyboardCallbackData


def get_start_kb(user: User, lang: Language):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang.keyboard.start.new_exchange, callback_data=KeyboardCallbackData.EXCHANGE_CREATE)],
        [InlineKeyboardButton(text=lang.keyboard.start.about_referal, callback_data="about_referal")],
        [InlineKeyboardButton(text=lang.keyboard.start.exchange_history, callback_data="exchange_history")],
        [InlineKeyboardButton(text=lang.keyboard.start.faq, callback_data=KeyboardCallbackData.FAQ)],
        [InlineKeyboardButton(text=lang.keyboard.start.change_lang, callback_data="change_lang")],
    ], resize_keyboard=True)

def get_language_keyboard(user: User, lang: Language):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang.keyboard.select_language.ru, callback_data=KeyboardCallbackData.SET_LANGUAGE + "ru")],
        [InlineKeyboardButton(text=lang.keyboard.select_language.en, callback_data=KeyboardCallbackData.SET_LANGUAGE + "en")]
    ])
