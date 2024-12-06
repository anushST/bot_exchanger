import re

from aiogram import Router, F, Bot
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src import keyboards
from src.lang import Language
from src.models import Currency, User, Transaction
from src.states import ExchangeForm
from src.utils import format_message
from src.config import KeyboardCallbackData

from src.api.executors import show_rate, process_transaction

router = Router()

class StoreObj:
    def __init__(self, user_id, is_fixed_rate, from_ccy, to_ccy, direction, amount, to_address):
        self.user_id = user_id
        self.type = 'fixed' if is_fixed_rate else 'float'
        self.from_ccy = from_ccy
        self.to_ccy = to_ccy
        self.direction = direction
        self.amount = amount
        self.to_address = to_address


async def format_exchange_info(lang: Language, state: dict, add = {}):
    return {
        "exchange_id": state.get("exchange_id"),
        "currency_from": state.get("currency_from_name"),
        "network_from": state.get("currency_from_network_name"),
        "currency_to": state.get("currency_to_name"),
        "network_to": state.get("currency_to_network_name"),
        "wallet": state.get("wallet_address"),
        "amount_currency": state.get("amount_currency"),
        "amount_value": state.get("amount_value"),

        "final_amount": state.get("final_amount", lang.exchange.searching),
        "rate_amount": state.get("rate_amount", lang.exchange.searching),
        "absolute_rate": state.get("absolute_rate", lang.exchange.searching),

        "rate_type": lang.exchange.rate.get("fixed" if state.get("is_fixed_rate") else "float"),

        'amount_from': add.get('from', None),
        'amount_to': add.get('to', None)
    }


@router.callback_query(F.data == KeyboardCallbackData.EXCHANGE_CREATE)
async def create(event: CallbackQuery, user: User, lang: Language, state: FSMContext, session: Session, bot: Bot):
    await state.set_state(ExchangeForm.is_fixed_rate)
    await bot.send_message(
        chat_id=event.from_user.id,
        text=format_message(
            lang.exchange.select_rate_mode,
            **await format_exchange_info(lang, await state.get_data())
        ), reply_markup=keyboards.exchange.get_rates_kb(lang)
    )
    await event.message.delete()


@router.callback_query(ExchangeForm.is_fixed_rate)
async def select_rate_type(event: CallbackQuery, lang: Language, state: FSMContext, bot: Bot, session: Session):
    is_fixed_rate = None
    if event.data == KeyboardCallbackData.EXCHANGE_FIX_RATE:
        is_fixed_rate = True
    elif event.data == KeyboardCallbackData.EXCHANGE_FLOAT_RATE:
        is_fixed_rate = False

    if is_fixed_rate is not None:
        await state.set_state(ExchangeForm.currency_from)
        await state.update_data(is_fixed_rate=is_fixed_rate)

        await event.message.delete()
        await bot.send_message(
            chat_id=event.from_user.id,
            text='Выберите валюту')


@router.message(ExchangeForm.currency_from)
async def select_currency_from(message: Message, lang: Language,
                               state: FSMContext, session: Session):
    currency = await session.execute(select(Currency).where(Currency.name == message.text))
    currencies = currency.scalars().first()
    if currencies:
        networks = currencies.network.split('|')
        await state.update_data(currency_from=currencies.code,
                                currency_from_name=currencies.name)
        if True:
            await state.set_state(ExchangeForm.currency_from_network)
            await message.answer(
                text='Выберите network',
                reply_markup=keyboards.exchange.get_networks_kb(lang, networks)
            )
        else:
            await state.update_data(currency_from_id=currencies.id)
            await state.set_state(ExchangeForm.currency_to)
            await message.answer(
                text='Выберите валюту которую хотите получить',
                reply_markup=keyboards.exchange.get_currencies_kb(lang, [])
            )
    else:
        await message.answer("неправильная валюта")


@router.message(ExchangeForm.currency_from_network)
async def select_network_from(message: Message, lang: Language, state: FSMContext, session: Session):
    currency_code = await state.get_value("currency_from")
    currency = await session.execute(select(Currency).where(Currency.code == currency_code))
    currency = currency.scalars().first()
    if currency:
        await state.set_state(ExchangeForm.currency_to)
        await state.update_data(currency_from_network=currency.network_code,
                                currency_from_network_name=currency.network,
                                currency_from_id=currency.id)

        await message.answer(
            text='Выберите валюту которую хотите получить',
            reply_markup=keyboards.exchange.get_currencies_kb(lang, [])
        )
    else:
        await message.answer("ERROR")


# ### TO ###

@router.message(ExchangeForm.currency_to)
async def select_currency_to(message: Message, lang: Language, state: FSMContext, session: Session):
    currency = await session.execute(select(Currency).where(Currency.name == message.text))
    currencies = currency.scalars().first()
    if currencies:
        networks = currencies.network.split('|')
        await state.update_data(currency_to=currencies.code, currency_to_name=currencies.name)
        if True:
            await state.set_state(ExchangeForm.currency_to_network)
            await message.answer(
                text=format_message('Выберите network'),
                reply_markup=keyboards.exchange.get_networks_kb(lang, networks)
            )
        else:
            await state.update_data(currency_to_id=networks[0].id)
            await state.set_state(ExchangeForm.wallet_address)
            await message.answer(text='Введите номер кошелёк')
    else:
        await message.answer("ERROR")


@router.message(ExchangeForm.currency_to_network)
async def select_network_to(message: Message, lang: Language, state: FSMContext, session: Session):
    currency_code = await state.get_value("currency_to")
    currency = await session.execute(select(Currency).where(Currency.code == currency_code))
    currency = currency.scalars().first()
    if currency:
        await state.set_state(ExchangeForm.wallet_address)
        await state.update_data(
            currency_to_network=currency.network_code,
            currency_to_network_name=currency.network,
            currency_to_id=currency.id
        )

        await message.answer(text='Введите номер кошелька')
    else:
        await message.answer("ERROR")


# ## WALLET ##

@router.message(ExchangeForm.wallet_address)
async def select_wallet(message: Message, lang: Language, state: FSMContext, session: Session):
    wallet = message.text.strip()
    if wallet:
        await state.set_state(ExchangeForm.amount_currency)
        await state.update_data(wallet_address=wallet)

        await message.answer(text=('Введите валюту операции'))
    else:
        await message.answer("ERROR")


@router.message(ExchangeForm.amount_currency)
async def select_amount_currency(message: Message, lang: Language, state: FSMContext, session: Session):
    currency = message.text.strip()
    data = await state.get_data()
    if currency:
        await state.set_state(ExchangeForm.amount_value)
        await state.update_data(amount_currency=currency)
        if data.get('currency_from'):
            await state.update_data(currency_direction='from')
        else:
            await state.update_data(currency_direction='to')
        await message.answer(text=('Введите количество'))
    else:
        await message.answer("ERROR")


@router.message(ExchangeForm.amount_value)
async def select_amount(message: Message, lang: Language, user, state: FSMContext, session: Session):
    amount = re.match("(\\d+(\\.\\d+)?)", message.text.strip().replace(",", "."))
    amount = round(float(amount.group()), 6) if amount else None

    if amount and amount > 0:
        await state.set_state(ExchangeForm.confirm)
        await state.update_data(amount_value=amount)
        data = await state.get_data()
        exchange = StoreObj(
            user_id=user.id,
            is_fixed_rate=data.get('is_fixed_rate'),
            from_ccy=data.get('currency_from'),
            to_ccy=data.get('currency_to'),
            direction=data.get('currency_direction'),
            amount=data.get('amount_value'),
            to_address= data.get('wallet_address'),
        )
        result = await show_rate(exchange)

        await message.answer(
            text=format_message(
                lang.exchange.confirm,
                **await format_exchange_info(lang, await state.get_data(), {
                    'from': result['from']['amount'],
                    'to': result['to']['amount']
                })
            ), reply_markup=keyboards.exchange.get_confirm_kb(lang)
        )
    else:
        await message.answer("ERROR")


@router.callback_query(ExchangeForm.confirm, F.data == KeyboardCallbackData.EXCHANGE_CONFIRM)
async def confirm(event: CallbackQuery, bot, user: User, lang: Language, state: FSMContext, session: Session):
    data = await state.get_data()
    import logging
    logging.critical(data)
    exchange = StoreObj(
        user_id=user.id,
        is_fixed_rate=data.get('is_fixed_rate'),
        from_ccy=data.get('currency_from'),
        to_ccy=data.get('currency_to'),
        direction=data.get('currency_direction'),
        amount=data.get('amount_value'),
        to_address= data.get('wallet_address'),
    )
    # session.add(exchange)
    # await session.commit()

    await event.message.edit_text(
        text='Запрос принят! Ждите', reply_markup=None
    )
    await process_transaction(exchange, bot, event.from_user.id)
