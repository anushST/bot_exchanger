from uuid import uuid4
from aiogram import Router, Bot
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import (InlineQueryResultArticle, InlineQueryResultPhoto,
                           InputTextMessageContent)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database import session
from src.models import Currency
from src.states import ExchangeForm

router = Router()


async def search_currency(session: AsyncSession, query: str):
    async with session() as ses:
        stmt = select(Currency)
        if query:
            stmt = stmt.filter(
                (Currency.name.ilike(f'%{query}%')) |
                (Currency.code.ilike(f'%{query}%'))
            )
        result = await ses.execute(stmt)
        return result.scalars().all()


@router.inline_query()
async def inline_query_handler(inline_query: types.InlineQuery, bot: Bot, state: FSMContext):
    query = inline_query.query or ''
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
    elif current_state in [ExchangeForm.currency_to, ExchangeForm.currency_from]:
        currencies = await search_currency(session, query)
        for currency in currencies:
            if currency.image_url:
                results.append(
                    InlineQueryResultPhoto(
                        id=str(uuid4()),
                        photo_url=currency.image_url,
                        thumbnail_url=currency.image_url,
                        title=f'{currency.name} ({currency.code})',
                        description=f'{currency.name} ({currency.code})',
                        caption='Hi there',
                        input_message_content=InputTextMessageContent(
                            message_text=f'{currency.code}'
                        )
                    )
                )
            else:
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title=f'{currency.name} ({currency.code})',
                        input_message_content=InputTextMessageContent(
                            message_text=f'{currency.code}'
                        )
                    )
                )

    await bot.answer_inline_query(inline_query.id, results, cache_time=0)