import re

from aiogram import Router, F, Bot
from sqlalchemy.orm import Session
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src import keyboards
from src.lang import Language
from src.models.user import User
from src.states import ExchangeForm
from src.utils import format_message
from src.config import KeyboardCallbackData

router = Router()


async def format_exchange_info(lang: Language, state: dict):
    return {
        "exchange_id": state.get("exchange_id"),
        "currency_from": state.get("currency_from_name"),
        "network_from": state.get("currency_from_network_name"),
        "currency_to": state.get("currency_to_name"),
        "network_to": state.get("currency_to_network_name"),
        "wallet": state.get("wallet_address"),
        "amount": state.get("amount"),

        "final_amount": state.get("final_amount", lang.exchange.searching),
        "rate_amount": state.get("rate_amount", lang.exchange.searching),
        "absolute_rate": state.get("absolute_rate", lang.exchange.searching),

        "rate_type": lang.exchange.rate.get("fixed" if state.get("is_fixed_rate") else "float"),
    }


@router.callback_query(F.data == KeyboardCallbackData.EXCHANGE_CREATE)
async def create(event: CallbackQuery, user: User, lang: Language, state: FSMContext, session: Session, bot: Bot):
    await state.set_state(ExchangeForm.is_fixed_rate)
    await event.message.edit_text(
        text=format_message(
            lang.exchange.select_rate_mode,
            **await format_exchange_info(lang, await state.get_data())
        ), reply_markup=keyboards.exchange.get_rates_kb(lang)
    )

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
            text=format_message(lang.exchange.select_from_currency),
            reply_markup=keyboards.exchange.get_currencies_kb(lang,
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        )


@router.message(ExchangeForm.currency_from)
async def select_currency_from(message: Message, lang: Language, state: FSMContext, session: Session):
    networks = session.query(Currency).filter_by(name=message.text).all()
    if networks:
        await state.update_data(currency_from=networks[0].code, currency_from_name=networks[0].name)
        if len(networks) > 1:
            await state.set_state(ExchangeForm.currency_from_network)
            await message.answer(
                text=format_message(lang.exchange.select_from_network, currency_from=networks[0].name),
                reply_markup=keyboards.exchange.get_networks_kb(lang, networks)
            )
        else:
            await state.update_data(currency_from_id=networks[0].id)
            await state.set_state(ExchangeForm.currency_to)
            await message.answer(
                text=format_message(lang.exchange.select_to_currency, **await format_exchange_info(lang, await state.get_data())),
                reply_markup=keyboards.exchange.get_currencies_kb(
                    lang, session.query(Currency).group_by(Currency.code).all())
            )
    else:
        await message.answer("ERROR")


@router.message(ExchangeForm.currency_from_network)
async def select_network_from(message: Message, lang: Language, state: FSMContext, session: Session):
    currency_code = await state.get_value("currency_from")
    currency = session.query(Currency).filter_by(code=currency_code, network=message.text).first()
    if currency:
        await state.set_state(ExchangeForm.currency_to)
        await state.update_data(currency_from_network=currency.network_code,
                                currency_from_network_name=currency.network,
                                currency_from_id=currency.id)

        await message.answer(
            text=format_message(lang.exchange.select_to_currency, **await format_exchange_info(lang, await state.get_data())),
            reply_markup=keyboards.exchange.get_currencies_kb(lang,
                                                              session.query(Currency).group_by(Currency.code).all())
        )
    else:
        await message.answer("ERROR")


### TO ###

@router.message(ExchangeForm.currency_to)
async def select_currency_to(message: Message, lang: Language, state: FSMContext, session: Session):
    networks = session.query(Currency).filter_by(name=message.text).all()
    if networks:
        await state.update_data(currency_to=networks[0].code, currency_to_name=networks[0].name)
        if len(networks) > 1:
            await state.set_state(ExchangeForm.currency_to_network)
            await message.answer(
                text=format_message(
                    lang.exchange.select_to_network,
                    **await format_exchange_info(lang, await state.get_data())
                ),
                reply_markup=keyboards.exchange.get_networks_kb(lang, networks)
            )
        else:
            await state.update_data(currency_to_id=networks[0].id)
            await state.set_state(ExchangeForm.wallet_address)
            await message.answer(
                text=format_message(
                    lang.exchange.select_wallet,
                    **await format_exchange_info(lang, await state.get_data())
                )
            )

    else:
        await message.answer("ERROR")


@router.message(ExchangeForm.currency_to_network)
async def select_network_to(message: Message, lang: Language, state: FSMContext, session: Session):
    currency_code = await state.get_value("currency_to")
    currency = session.query(Currency).filter_by(code=currency_code, network=message.text).first()
    if currency:
        await state.set_state(ExchangeForm.wallet_address)
        await state.update_data(
            currency_to_network=currency.network_code,
            currency_to_network_name=currency.network,
            currency_to_id=currency.id
        )

        await message.answer(
            text=format_message(
                lang.exchange.select_wallet,
                **await format_exchange_info(lang, await state.get_data())
            )
        )
    else:
        await message.answer("ERROR")


## WALLET ##

@router.message(ExchangeForm.wallet_address)
async def select_wallet(message: Message, lang: Language, state: FSMContext, session: Session):
    wallet = message.text.strip()
    if wallet:
        await state.set_state(ExchangeForm.amount)
        await state.update_data(wallet_address=wallet)

        await message.answer(
            text=format_message(
                lang.exchange.select_amount,
                **await format_exchange_info(lang, await state.get_data())
            )
        )
    else:
        await message.answer("ERROR")


@router.message(ExchangeForm.amount)
async def select_amount(message: Message, lang: Language, state: FSMContext, session: Session):
    amount = re.match("(\\d+(\\.\\d+)?)", message.text.strip().replace(",", "."))
    amount = round(float(amount.group()), 6) if amount else None

    if amount and amount > 0:
        await state.set_state(ExchangeForm.confirm)
        await state.update_data(amount=amount)

        await message.answer(
            text=format_message(
                lang.exchange.confirm,
                **await format_exchange_info(lang, await state.get_data())
            ), reply_markup=keyboards.exchange.get_confirm_kb(lang)
        )
    else:
        await message.answer("ERROR")


@router.callback_query(ExchangeForm.confirm, F.data == KeyboardCallbackData.EXCHANGE_CONFIRM)
async def confirm(event: CallbackQuery, user: User, lang: Language, state: FSMContext, session: Session):
    data = await state.get_data()
    exchange = Exchange(
        user_id=user.id,
        is_fixed_rate=data.get("is_fixed_rate"),
        currency_from_id=data.get("currency_from_id"),
        currency_to_id=data.get("currency_to_id"),
        origin_amount=data.get("amount"),
        wallet=data.get("wallet"),
    )
    session.add(exchange)
    session.commit()

    await state.set_state(ExchangeForm.exchange_id)
    await state.update_data(confirm=True, exchange_id=exchange.id)

    await event.message.edit_text(
        text=format_message(
            lang.exchange.exchange_status,
            status=lang.exchange.status.searching,
            **await format_exchange_info(lang, await state.get_data())
        ), reply_markup=None
    )

    import time
    time.sleep(5)

    await state.update_data(final_amount=100)
    await state.update_data(rate_amount=100)
    await state.update_data(absolute_rate=100)

    await event.message.edit_text(
        text=format_message(
            lang.exchange.exchange_status,
            status=lang.exchange.status.wait_confirm,
            **await format_exchange_info(lang, await state.get_data())
        ), reply_markup=keyboards.exchange.get_confirm_kb(lang)
    )
