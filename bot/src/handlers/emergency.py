import logging
import re

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from . import constants as c
from src import exceptions as ex
from src.keyboards import exchange as exchange_kbs
from src.api.ffio import ffio_redis_client as frc, schemas
from src.lang import Language
from src.models import EmergencyChoices, Transaction
from src.states import ExchangeForm
from src.utils import format_message
from src.config import KeyboardCallbackData

router = Router()

logger = logging.getLogger(__name__)


async def fetch_transaction(session: AsyncSession,
                            transaction_id: str) -> Transaction:
    try:
        result = await session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return result.scalars().first()
    except Exception as e:
        logger.error(f"Error fetching transaction {transaction_id}: {e}")
        return None


async def update_transaction(session: AsyncSession, transaction: Transaction,
                             **kwargs):
    try:
        for key, value in kwargs.items():
            setattr(transaction, key, value)
        await session.commit()
        await session.refresh(transaction)
    except Exception as e:
        logger.error(f"Error updating transaction {transaction.id}: {e}")
        raise


@router.callback_query(
    F.data.regexp(fr'^{KeyboardCallbackData.EMERGENCY_EXCHANGE}'))
async def handle_exchange_choice(event: CallbackQuery, lang: Language,
                                 session: AsyncSession):
    try:
        data = event.data.split(':')
        if len(data) < 1:
            logger.error(f"Invalid data format: {event.data}")
            return

        transaction_id = data[1]
        transaction = await fetch_transaction(session, transaction_id)

        if not transaction:
            raise ex.TransactionDoesNotExistError(
                'Transaction does not exist.')

        await update_transaction(
            session, transaction, emergency_choise=EmergencyChoices.EXCHANGE)

        await event.message.edit_text(
            text=lang.transaction.emergency.exchange
        )
        logger.info(f"Transaction {transaction_id} updated successfully.")
    except Exception:
        raise


@router.callback_query(  # ToDo
        F.data.regexp(fr'^{KeyboardCallbackData.EMERGENCY_REFUND}'))
async def handle_refund_choice(event: CallbackQuery, lang: Language,
                               state: FSMContext, bot: Bot,
                               session: AsyncSession):
    try:
        data = event.data.split(':')
        if len(data) < 1:
            logger.error(f"Invalid data format: {event.data}")
            return

        transaction_id = data[1]
        transaction = await fetch_transaction(session, transaction_id)

        if not transaction:
            logger.warning(f"Transaction not found: ID {transaction_id}")
            return

        await state.update_data(emergency_transaction_id=transaction_id)
        await state.set_state(ExchangeForm.emergency_address)

        await event.message.edit_text(
            text=event.message.text
        )
        await bot.send_message(
            chat_id=event.from_user.id,
            text=format_message(lang.transaction.emergency.address,
                                **transaction.to_dict())
        )
        logger.info(f"Transaction {transaction_id} updated successfully.")

    except Exception as e:
        logger.error(f"Error handling refund choice: {e}")
        raise


@router.message(ExchangeForm.emergency_address)
async def emergency_address_handler(message: Message, lang: Language,
                                    state: FSMContext, bot: Bot,
                                    session: AsyncSession):
    try:
        logger.info('Handling emergency address')
        state_data = await state.get_data()
        transaction_id = state_data.get('emergency_transaction_id')
        address = message.text

        transaction = await fetch_transaction(session, transaction_id)
        if not transaction:
            logger.warning(f"Transaction not found: ID {transaction_id}")
            return

        if transaction.final_from_tag_name:
            await state.update_data(emergency_address=address)
            await state.set_state(ExchangeForm.emergency_tag)
            text = format_message(lang.transaction.emergency.tag,
                                  **transaction.to_dict())
        else:
            await update_transaction(session, transaction,
                                     emergency_choise=EmergencyChoices.REFUND,
                                     emergency_address=address,
                                     made_emergency_action=True)
            await state.clear()
            text = format_message(lang.transaction.emergency.accepted)

        await bot.send_message(
            chat_id=message.from_user.id,
            text=text
        )

    except Exception as e:
        logger.error(f"Error handling emergency address: {e}")
        raise


@router.message(ExchangeForm.emergency_tag)
async def emergency_tag_handler(message: Message, lang: Language,
                                state: FSMContext, bot: Bot,
                                session: AsyncSession):
    try:
        state_data = await state.get_data()
        transaction_id = state_data.get('emergency_transaction_id')
        tag_value = message.text

        transaction = await fetch_transaction(session, transaction_id)
        if not transaction:
            logger.warning(f"Transaction not found: ID {transaction_id}")
            return

        await update_transaction(
            session, transaction,
            emergency_choise=EmergencyChoices.REFUND,
            emergency_address=state_data.get('emergency_address'),
            emergency_tag_name=transaction.final_from_tag_name,
            emergency_tag_value=tag_value,
            made_emergency_action=True
        )
        await bot.send_message(
            chat_id=message.from_user.id,
            text=format_message(lang.transaction.emergency.accepted)
        )

        await state.clear()
    except Exception as e:
        logger.error(f"Error handling emergency tag: {e}")
        raise


@router.callback_query(
        F.data.regexp(fr'^{KeyboardCallbackData.EMERGENCY_RETRY_ADDRESS}'))
async def retry_address(event: CallbackQuery, lang: Language, bot: Bot,
                        state: FSMContext, session: AsyncSession):
    try:
        data = event.data.split(':')
        if len(data) < 1:
            logger.error(f"Invalid data format: {event.data}")
            return

        transaction_id = data[1]
        transaction = await fetch_transaction(session, transaction_id)

        if not transaction:
            logger.warning(f"Transaction not found: ID {transaction_id}")
            return
        await event.message.edit_text(
            text=event.message.text, reply_markup=None
        )
        await state.update_data(emergency_transaction_id=transaction_id)
        await state.set_state(ExchangeForm.emergency_address)
        await bot.send_message(
            chat_id=event.from_user.id,
            text=format_message(lang.transaction.emergency.address,
                                **transaction.to_dict())
        )
    except Exception:
        raise
