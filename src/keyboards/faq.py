from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from src.lang import Language
from src.models.user import User
from src.config import KeyboardCallbackData

def get_main_kb(user: User, lang: Language):
    return InlineKeyboardMarkup(inline_keyboard=[
        *[[InlineKeyboardButton(
            text=lang.keyboard.faq.get(f"q{question_id}"), callback_data=KeyboardCallbackData.get_faq_question(question_id)
        )] for question_id in range(1, 8)],
        [InlineKeyboardButton(text=lang.keyboard.general.prev, callback_data=KeyboardCallbackData.START)]
    ])

def get_question_kb(user: User, lang: Language):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang.keyboard.faq.exit, callback_data=KeyboardCallbackData.START)],
        [InlineKeyboardButton(text=lang.keyboard.faq.other_questions, callback_data=KeyboardCallbackData.FAQ)],
    ])