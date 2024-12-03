from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src import keyboards
from src.filters.text import MultilanguageTextFilter
from src.lang import Language
from src.models.user import User
from src.utils import format_message
from src.config import KeyboardCallbackData

router = Router()

@router.message(CommandStart())
async def main(message: Message, user: User, lang: Language):
    await message.answer(
        format_message(lang.start, user_name=user.tg_name),
        reply_markup=keyboards.main.get_start_kb(user, lang)
    )

@router.message(MultilanguageTextFilter("keyboard.general.cancel"))
async def cancel(message: Message, user: User, lang: Language, state: FSMContext):
    await state.clear()
    await main(message, user, lang)

@router.callback_query(F.data == KeyboardCallbackData.START)
async def main_cb(query: CallbackQuery, user: User, lang: Language):
    await query.message.edit_text(
        format_message(lang.start, user_name=user.tg_name),
        reply_markup=keyboards.main.get_start_kb(user, lang)
    )

@router.callback_query(F.data == KeyboardCallbackData.CANCEL)
async def cancel_cb(query: CallbackQuery, user: User, lang: Language, state: FSMContext):
    await state.clear()
    await main_cb(query, user, lang)

@router.callback_query(F.data == KeyboardCallbackData.CHANGE_LANGUAGE)
async def change_language(query: CallbackQuery, user: User, lang: Language):
    await query.message.edit_text(
        format_message(lang.select_language, user_name=user.tg_name),
        reply_markup=keyboards.main.get_language_keyboard(user, lang)
    )

@router.callback_query(F.data.startswith(KeyboardCallbackData.SET_LANGUAGE))
async def set_language(query: CallbackQuery, user: User):
    language_code = query.data.removeprefix(KeyboardCallbackData.SET_LANGUAGE).lower()
    user.language = language_code
    lang = user.get_lang()
    await main_cb(query, user, lang)
