from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.lang import Language
from src.config import KeyboardCallbackData


def get_emergency_choice_kb(lang: Language, transaction_id: str,
                            has_exchange: bool = True):
    keyboard = [
        [InlineKeyboardButton(
            text=lang.keyboard.emergency.refund,
            callback_data=(f'{KeyboardCallbackData.EMERGENCY_REFUND}'
                           f'{transaction_id}'),)],
    ]
    if has_exchange:
        keyboard.append(
            [InlineKeyboardButton(
                text=lang.keyboard.emergency.exchange,
                callback_data=(f'{KeyboardCallbackData.EMERGENCY_EXCHANGE}'
                               f'{transaction_id}'))],
        )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_again_address_kb(lang: Language, transaction_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=lang.keyboard.retry_emergency_address,
            callback_data=(f'{KeyboardCallbackData.EMERGENCY_RETRY_ADDRESS}'
                           f'{transaction_id}')
        )]
    ])
