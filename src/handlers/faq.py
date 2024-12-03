from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from src import keyboards
from src.lang import Language
from src.models.user import User
from src.utils import format_message
from src.config import KeyboardCallbackData

router = Router()

@router.callback_query(F.data == KeyboardCallbackData.FAQ)
async def main(query: CallbackQuery, user: User, lang: Language):
    await query.message.edit_text(lang.faq, reply_markup=keyboards.faq.get_main_kb(user, lang))

@router.callback_query(F.data.startswith(KeyboardCallbackData.FAQ_QUESTION))
async def get(query: CallbackQuery, user: User, lang: Language):
    question_id = query.data.removeprefix(KeyboardCallbackData.FAQ_QUESTION)
    answer = lang.faq_answers.get("q" + question_id)
    if answer:
        await query.message.edit_text(answer, reply_markup=keyboards.faq.get_question_kb(user, lang))

