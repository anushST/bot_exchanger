from uuid import uuid4
from aiogram import Router, Bot
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import (InlineQueryResultArticle,
                           InputTextMessageContent)

from src.api.ffio import ffio_redis_client as frc
from src.states import ExchangeForm

router = Router()


@router.inline_query()
async def inline_query_handler(inline_query: types.InlineQuery, bot: Bot,
                               state: FSMContext):
    results = []

    current_state = await state.get_state()
    data = await state.get_data()

    if current_state == ExchangeForm.amount_currency:
        currencies = [
            {'name': data.get('currency_from')},
            {'name': data.get('currency_to')}
        ]
        for currency in currencies:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=f'{currency['name']}',
                    input_message_content=InputTextMessageContent(
                            message_text=f'{currency['name']}'
                        )
                )
            )
    elif current_state in [ExchangeForm.currency_to,
                           ExchangeForm.currency_from]:
        user_query = (inline_query.query or '').lower()
        currencies = await frc.get_coins()
        if user_query:
            currencies = [
                currency for currency in currencies if currency.lower().startswith(user_query) # noqa
            ]
        for currency in currencies:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=currency,
                    input_message_content=InputTextMessageContent(
                        message_text=currency
                    )
                )
            )

    await bot.answer_inline_query(inline_query.id, results, cache_time=0)
