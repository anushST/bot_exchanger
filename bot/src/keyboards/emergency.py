from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.lang import Language
from src.config import KeyboardCallbackData


def get_emergency_choice_kb(lang: Language, transaction_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=lang.keyboard.emergency.exchange,
            callback_data=(f'{KeyboardCallbackData.EMERGENCY_EXCHANGE}'
                           f'{transaction_id}'))],
        [InlineKeyboardButton(
            text=lang.keyboard.emergency.refund,
            callback_data=(f'{KeyboardCallbackData.EMERGENCY_REFUND}'
                           f'{transaction_id}'),)],
    ])
