from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from src.lang import Language
from src.models.user import User
from src.config import KeyboardCallbackData


def get_cancel_kb(lang: Language):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang.keyboard.general.cancel, callback_data=KeyboardCallbackData.CANCEL)],
    ], resize_keyboard=True)

def get_currencies_kb(lang: Language, currencies: list):
    return ReplyKeyboardMarkup(keyboard=[
        *[[KeyboardButton(text=c.name)] for c in currencies],
        [KeyboardButton(text=lang.keyboard.general.cancel)]
    ], resize_keyboard=True, one_time_keyboard=True)

def get_networks_kb(lang: Language, currencies: list):
    return ReplyKeyboardMarkup(keyboard=[
        *[[KeyboardButton(text=c.network)] for c in currencies],
        [KeyboardButton(text=lang.keyboard.general.cancel)]
    ], resize_keyboard=True, one_time_keyboard=True)

def get_rates_kb(lang: Language):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang.keyboard.exchange.fix_rate, callback_data=KeyboardCallbackData.EXCHANGE_FIX_RATE)],
        [InlineKeyboardButton(text=lang.keyboard.exchange.float_rate, callback_data=KeyboardCallbackData.EXCHANGE_FLOAT_RATE)],
        [InlineKeyboardButton(text=lang.keyboard.general.cancel, callback_data=KeyboardCallbackData.CANCEL)]
    ])

def get_confirm_kb(lang: Language):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang.keyboard.exchange.confirm, callback_data=KeyboardCallbackData.EXCHANGE_CONFIRM)],
        [InlineKeyboardButton(text=lang.keyboard.general.cancel, callback_data=KeyboardCallbackData.CANCEL)]
    ])
