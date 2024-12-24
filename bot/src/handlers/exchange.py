import logging
from decimal import Decimal, InvalidOperation

from aiogram import Router, F, Bot
from sqlalchemy.orm import Session
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from . import constants as c
from src.keyboards import exchange as exchange_kbs
from src.api.ffio import ffio_redis_client as frc, schemas
from src.lang import Language
from src.models import DirectionTypes, RateTypes, Transaction, User
from src.states import ExchangeForm
from src.utils import format_message
from src.config import KeyboardCallbackData

router = Router()

logger = logging.getLogger(__name__)


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
        'tag_name': state.get('tag_name'),
        'tag_value': state.get('tag_value'),

        # "final_amount": state.get("final_amount", lang.exchange.searching),
        # "rate_amount": state.get("rate_amount", lang.exchange.searching),
        # "absolute_rate": state.get("absolute_rate", lang.exchange.searching),
    }


async def get_rate(state_data: dict) -> schemas.RatesSchema:
    """Fetch exchange rate with validation and logging."""
    # List of required fields in the input data
    required_fields = [
        'currency_from', 'currency_to',
        'currency_from_network', 'currency_to_network',
        'rate_type'
    ]

    # Validate the presence of all required fields
    for field in required_fields:
        if field not in state_data:
            raise ValueError(f'Missing required field: {field}')

    currency_from = state_data['currency_from']
    currency_to = state_data['currency_to']
    currency_from_network = state_data['currency_from_network']
    currency_to_network = state_data['currency_to_network']
    rate_type = state_data['rate_type']

    if rate_type == RateTypes.FIXED:
        rate = await frc.get_fixed_rate(
            currency_from,
            currency_from_network,
            currency_to,
            currency_to_network
        )
    elif rate_type == RateTypes.FLOAT:
        rate = await frc.get_float_rate(
            currency_from,
            currency_from_network,
            currency_to,
            currency_to_network
        )
    else:
        logger.error('Invalid rate type')
        raise ValueError('Invalid rate type')

    if not rate or not hasattr(rate, 'min_amount') or not hasattr(
            rate, 'max_amount'):
        raise ValueError('Invalid rate. Please check the input data.')
    return rate


@router.callback_query(F.data == KeyboardCallbackData.EXCHANGE_CREATE)
async def create(event: CallbackQuery, lang: Language, state: FSMContext,
                 bot: Bot):
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
                           state: FSMContext, bot: Bot):
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
                **await format_exchange_info(lang, await state.get_data())
            ),
            reply_markup=exchange_kbs.get_search_kb(lang)
        )
    else:
        await bot.send_message(
            chat_id=event.from_user.id,
            text=lang.exchange.invalid_rate_type
        )


@router.message(ExchangeForm.currency_from)
async def select_currency_from(message: Message, lang: Language,
                               state: FSMContext, session: Session):
    currencies = await frc.get_coins()
    currency = message.text
    if currency in currencies:
        networks = await frc.get_networks(currency)
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
    networks = await frc.get_networks(currency)
    network = message.text

    if network in networks:
        currency_info = await frc.get_coin_full_info(
            currency, network
        )
        if not currency_info.recv:
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
    currencies = await frc.get_coins()
    currency = message.text
    if currency in currencies:
        networks = await frc.get_networks(currency)
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
    networks = await frc.get_networks(currency)
    network = message.text
    currency_from = await state.get_value("currency_from")
    network_from = await state.get_value('currency_from_network')
    if network in networks:
        if currency_from == currency and network == network_from:
            await message.answer(lang.exchange.same_currency_error)
            return
        currency_info = await frc.get_coin_full_info(
            currency, network
        )
        if not currency_info.send:
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

async def select_amount_message(message: Message, data: dict,
                                state: FSMContext, lang: Language):
    rate_type = data.get('rate_type')

    if rate_type == RateTypes.FIXED:
        await state.set_state(ExchangeForm.amount_currency)
        await message.answer(
            text=format_message(
                lang.exchange.select_amount_currency,
                **await format_exchange_info(
                    lang, await state.get_data())),
            reply_markup=exchange_kbs.get_search_kb(lang))
    elif rate_type == RateTypes.FLOAT:
        await state.set_state(ExchangeForm.amount_value)
        currency_from = data.get('currency_from')
        currency_to = data.get('currency_to')
        await state.update_data(
            exchange_direction=DirectionTypes.FROM
        )
        currency = currency_from
        rate = await get_rate(data)
        text = lang.exchange.select_amount_from
        min_amount = rate.min_amount
        max_amount = rate.max_amount
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
    else:
        raise Exception('Rate type did not set.')


@router.message(ExchangeForm.wallet_address)
async def select_wallet(message: Message, lang: Language, state: FSMContext):
    wallet = message.text.strip()
    data = await state.get_data()
    currency_to = data.get('currency_to')
    network_to = data.get('currency_to_network')

    if wallet:
        await state.update_data(wallet_address=wallet)

        coin = await frc.get_coin_full_info(currency_to, network_to)
        if coin.tag is not None:
            await state.set_state(ExchangeForm.tag)
            await state.update_data(tag_name=coin.tag)
            await message.answer(
                text=format_message(lang.exchange.select_tag,
                                    tag_name=coin.tag)
            )
            return

        await select_amount_message(message, data, state, lang)
    else:
        await message.answer(lang.exchange.empty_wallet_error)


@router.message(ExchangeForm.tag)
async def select_tag(message: Message, lang: Language, state: FSMContext):
    tag = message.text.strip()
    data = await state.get_data()

    if not tag or tag == c.EMPTY_TAG_IDENTIFIER:
        await state.update_data(tag_value=None)
    else:
        await state.update_data(tag_value=tag)

    await select_amount_message(message, data, state, lang)


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
    logger.info(rate)

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
async def select_amount(message: Message, lang: Language,
                        state: FSMContext):
    amount = message.text
    try:
        amount = Decimal(amount)
    except InvalidOperation:
        await message.answer(lang.exchange.incorrect_amount)
        return

    state_data = await state.get_data()
    exchange_direction = state_data.get('exchange_direction')
    rate = await get_rate(state_data)

    # if not rate.check_min_max_limits(exchange_direction, amount):
    #     await message.answer(format_message(
    #         lang.exchange.amount_not_in_range,
    #     ))
    #     return

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

    if state_data.get('tag_name'):
        confirm_text = lang.exchange.confirm_with_tag
    else:
        confirm_text = lang.exchange.confirm

    await message.answer(
        text=format_message(
            confirm_text,
            amount_from=amount_from,
            amount_to=amount_to,
            **await format_exchange_info(lang, await state.get_data())
        ),
        reply_markup=exchange_kbs.get_confirm_kb(lang)
    )


@router.callback_query(ExchangeForm.confirm,
                       F.data == KeyboardCallbackData.EXCHANGE_CONFIRM)
async def confirm(event: CallbackQuery, bot: Bot, user: User, lang: Language,
                  state: FSMContext, session: Session):
    data = await state.get_data()
    exchange = Transaction(
        user_id=user.id,
        name=await Transaction.create_unique_name(session),
        rate_type=data.get('rate_type'),
        from_currency=data.get('currency_from'),
        from_currency_network=data.get('currency_from_network'),
        to_currency=data.get('currency_to'),
        to_currency_network=data.get('currency_to_network'),
        direction=data.get('exchange_direction'),
        amount=data.get('amount_value'),
        to_address=data.get('wallet_address'),
        tag_value=data.get('tag_value'),
        tag_name=data.get('tag_name'),
    )
    session.add(exchange)
    await session.commit()
    await event.message.edit_text(event.message.text, reply_markup=None)

    await bot.send_message(
        chat_id=event.from_user.id,
        text=lang.exchange.transaction_started,
        reply_markup=None)
