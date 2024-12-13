from decimal import Decimal, InvalidOperation

from aiogram import Router, F, Bot
from sqlalchemy.orm import Session
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.keyboards import exchange as exchange_kbs
from src.api.ffio import schemas, FFIORedisClient
from src.lang import Language
from src.models import DirectionTypes, RateTypes, User
from src.states import ExchangeForm
from src.utils import format_message
from src.config import KeyboardCallbackData


router = Router()
ffio_client = FFIORedisClient()


async def format_exchange_info(lang: Language, state: dict):
    return {
        "exchange_id": state.get('exchange_id'),
        'rate_type': state.get('rate_type'),

        "currency_from": state.get("currency_from"),
        "network_from": state.get("currency_from_network"),
        'currency_from_nickname': state.get('currency_from_nickname'),

        "currency_to": state.get("currency_to"),
        "network_to": state.get("currency_to_network"),
        'network_to_nickname': state.get('network_to_nickname'),

        "wallet": state.get("wallet_address"),
        "amount_currency": state.get("amount_currency"),
        "amount_value": state.get("amount_value"),

        # "final_amount": state.get("final_amount", lang.exchange.searching),
        # "rate_amount": state.get("rate_amount", lang.exchange.searching),
        # "absolute_rate": state.get("absolute_rate", lang.exchange.searching),
    }


async def get_rate(state_data: dict) -> schemas.RatesSchema:
    """Important! state_data has_to contain: currency_from, currency_to
    currency_from_network, currency_to_network, rate_type informations."""
    currency_from = state_data.get('currency_from')
    currency_to = state_data.get('currency_to')
    currency_from_network = state_data.get('currency_from_network')
    currency_to_network = state_data.get('currency_to_network')

    rate_type = state_data.get('rate_type')
    if rate_type == RateTypes.FIXED:
        rate = await ffio_client.get_fixed_rate(
            currency_from,
            currency_from_network,
            currency_to,
            currency_to_network)
    elif rate_type == RateTypes.FLOAT:
        rate = await ffio_client.get_flaot_rate(
            currency_from,
            currency_from_network,
            currency_to,
            currency_to_network)
    else:
        raise Exception('Rate type did not chosen')

    if not rate:
        raise Exception('Get_rate can not return empty rate list. '
                        'Please enter valid data.')
    return rate



@router.callback_query(F.data == KeyboardCallbackData.EXCHANGE_CREATE)
async def create(event: CallbackQuery, user: User, lang: Language,
                 state: FSMContext, session: Session, bot: Bot):
    await state.set_state(ExchangeForm.rate_type)
    await bot.send_message(
        chat_id=event.from_user.id,
        text=format_message(
            lang.exchange.select_rate_mode,
            **await format_exchange_info(lang, await state.get_data())
        ), reply_markup=exchange_kbs.get_rates_kb(lang)
    )
    await event.message.delete()


@router.callback_query(ExchangeForm.rate_type)
async def select_rate_type(event: CallbackQuery, lang: Language,
                           state: FSMContext, bot: Bot, session: Session):
    rate_type = None
    if event.data == KeyboardCallbackData.EXCHANGE_FIX_RATE:
        rate_type = RateTypes.FIXED
    elif event.data == KeyboardCallbackData.EXCHANGE_FLOAT_RATE:
        rate_type = RateTypes.FLOAT

    if rate_type is not None:
        await state.set_state(ExchangeForm.currency_from)
        await state.update_data(rate_type=rate_type)

        await event.message.delete()
        await bot.send_message(
            chat_id=event.from_user.id,
            text=format_message(
                lang.exchange.select_from_currency,
                **await format_exchange_info(lang, await state.get_data())),
            reply_markup=exchange_kbs.get_search_kb(lang))


@router.message(ExchangeForm.currency_from)
async def select_currency_from(message: Message, lang: Language,
                               state: FSMContext, session: Session):
    currencies = await ffio_client.get_coins()
    currency = message.text
    if currency in currencies:
        networks = await ffio_client.get_networks(currency)
        await state.update_data(currency_from=currency)
        await state.set_state(ExchangeForm.currency_from_network)
        await message.answer(
            text=format_message(
                lang.exchange.select_from_network,
                **await format_exchange_info(lang, await state.get_data())),
            reply_markup=exchange_kbs.get_networks_kb(lang, networks)
        )
    else:
        await message.answer(lang.exchange.incorrect_currency)


@router.message(ExchangeForm.currency_from_network)
async def select_network_from(message: Message, lang: Language,
                              state: FSMContext, session: Session):
    currency = await state.get_value("currency_from")
    networks = await ffio_client.get_networks(currency)
    network = message.text
    if network in networks:
        currency_info = await ffio_client.get_coin_full_info(
            currency, network
        )
        if not currency_info.send:
            await message.answer(lang.exchange.tech_workings,
                                 reply_markup=exchange_kbs.get_search_kb(lang))
            await state.set_state(ExchangeForm.currency_from)
            return
        await state.set_state(ExchangeForm.currency_to)
        await state.update_data(currency_from_network=network)

        await message.answer(
            text=format_message(
                lang.exchange.select_to_currency,
                **await format_exchange_info(lang, await state.get_data())),
            reply_markup=exchange_kbs.get_search_kb(lang)
        )
    else:
        await message.answer(lang.exchange.incorrect_network)


# ### TO ###

@router.message(ExchangeForm.currency_to)
async def select_currency_to(message: Message, lang: Language,
                             state: FSMContext, session: Session):
    currencies = await ffio_client.get_coins()
    currency = message.text
    currency_from = await state.get_value("currency_from")
    if currency_from == currency:
        await message.answer(lang.exchange.same_currency_error)
        return
    if currency in currencies:
        networks = await ffio_client.get_networks(currency)
        await state.update_data(currency_to=currency)
        await state.set_state(ExchangeForm.currency_to_network)
        await message.answer(
            text=format_message(
                lang.exchange.select_to_network,
                **await format_exchange_info(lang, await state.get_data())),
            reply_markup=exchange_kbs.get_networks_kb(lang, networks)
        )
    else:
        await message.answer(lang.exchange.incorrect_currency)


@router.message(ExchangeForm.currency_to_network)
async def select_network_to(message: Message, lang: Language,
                            state: FSMContext):
    currency = await state.get_value('currency_to')
    networks = await ffio_client.get_networks(currency)
    network = message.text
    if network in networks:
        currency_info = await ffio_client.get_coin_full_info(
            currency, network
        )
        if not currency_info.recv:
            await message.answer(lang.exchange.tech_workings,
                                 reply_markup=exchange_kbs.get_search_kb(lang))
            await state.set_state(ExchangeForm.currency_to)
            return
        await state.set_state(ExchangeForm.wallet_address)
        await state.update_data(currency_to_network=network)

        await message.answer(
            text=format_message(
                lang.exchange.select_wallet,
                **await format_exchange_info(lang, await state.get_data()))
        )
    else:
        await message.answer(lang.exchange.incorrect_network)


# ## WALLET ##

@router.message(ExchangeForm.wallet_address)
async def select_wallet(message: Message, lang: Language, state: FSMContext):
    wallet = message.text.strip()
    if wallet:
        await state.set_state(ExchangeForm.amount_currency)
        await state.update_data(wallet_address=wallet)

        await message.answer(
            text=format_message(
                lang.exchange.select_amount_currency,
                **await format_exchange_info(lang, await state.get_data())),
            reply_markup=exchange_kbs.get_search_kb(lang))
    else:
        await message.answer("ERROR")


@router.message(ExchangeForm.amount_currency)
async def select_amount_currency(message: Message, lang: Language,
                                 state: FSMContext):
    currency = message.text.strip()
    data = await state.get_data()
    currency_from = data.get('currency_from')
    currency_to = data.get('currency_to')

    if currency not in (currency_from, currency_to):
        await message.answer(text=lang.exchange.incorrect_amount_currency)
        return

    rate = await get_rate(data)

    if currency == currency_from:
        exchange_direction = DirectionTypes.FROM
        text = lang.exchange.select_amount_from
        min_amount = rate.min_amount
        max_amount = rate.max_amount
    else:
        exchange_direction = DirectionTypes.TO
        text = lang.exchange.select_amount_to
        min_amount = rate.get_to_min_amount()
        max_amount = rate.get_to_max_amount()

    await state.set_state(ExchangeForm.amount_value)
    await state.update_data()
    await state.update_data(
        amount_currency=currency,
        exchange_direction=exchange_direction
    )

    await message.answer(text=format_message(
        text,
        currency_from=currency_from,
        currency_from_in=rate.in_amount,
        currency_to=currency_to,
        currency_to_out=rate.out_amount,
        currency=currency,
        minamount=min_amount,
        maxamount=max_amount
    ))


@router.message(ExchangeForm.amount_value)
async def select_amount(message: Message, lang: Language, state: FSMContext):
    amount = message.text
    try:
        amount = Decimal(amount)
    except InvalidOperation:
        await message.answer(lang.exchange.incorrect_amount)
        return

    state_data = await state.get_data()
    exchange_direction = state_data.get('exchange_direction')
    rate = await get_rate(state_data)

    if not rate.check_min_max_limits(exchange_direction, amount):
        await message.answer(format_message(
            lang.exchange.amount_not_in_range,
        ))
        return

    if exchange_direction == DirectionTypes.FROM:
        amount_from = amount
        amount_to = rate.calculate_to_amount(amount)
    elif exchange_direction == DirectionTypes.TO:
        amount_from = rate.calculate_from_amount(amount)
        amount_to = amount
    else:
        raise Exception('Incorrect direction')

    await state.set_state(ExchangeForm.confirm)
    await state.update_data(amount_value=amount)

    await message.answer(
        text=format_message(
            lang.exchange.confirm,
            amount_from=amount_from,
            amount_to=amount_to,
            **await format_exchange_info(lang, await state.get_data())
        ),
        reply_markup=exchange_kbs.get_confirm_kb(lang)
    )


# @router.callback_query(ExchangeForm.confirm, F.data == KeyboardCallbackData.EXCHANGE_CONFIRM)
# async def confirm(event: CallbackQuery, bot, user: User, lang: Language, state: FSMContext, session: Session):
#     data = await state.get_data()
#     import logging
#     logging.critical(data)
#     exchange = StoreObj(
#         user_id=user.id,
#         is_fixed_rate=data.get('is_fixed_rate'),
#         from_ccy=data.get('currency_from'),
#         to_ccy=data.get('currency_to'),
#         direction=data.get('currency_direction'),
#         amount=data.get('amount_value'),
#         to_address= data.get('wallet_address'),
#     )
#     # session.add(exchange)
#     # await session.commit()

#     await event.message.edit_text(
#         text='Запрос принят! Ждите', reply_markup=None
#     )
#     await process_transaction(exchange, bot, event.from_user.id)
