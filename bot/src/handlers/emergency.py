import logging
import re

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from . import constants as c
from src.keyboards import exchange as exchange_kbs
from src.api.ffio import ffio_redis_client as frc, schemas
from src.lang import Language
from src.models import EmergencyChoices, Transaction
from src.states import ExchangeForm
from src.utils import format_message
from src.config import KeyboardCallbackData

router = Router()

logger = logging.getLogger(__name__)


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
        result = await session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        transaction: Transaction = result.scalars().first()

        if not transaction:
            logger.warning(f"Transaction not found: ID {transaction_id}")
            return

        transaction.emergency_choise = EmergencyChoices.EXCHANGE
        await session.commit()
        await session.refresh(transaction)

        await event.message.edit_text(
            text=lang.transaction.emergency_exchange
        )
        logger.info(f"Transaction {transaction_id} updated successfully.")
    except Exception:
        raise



@router.callback_query(
        F.data.regexp(fr'^{KeyboardCallbackData.EMERGENCY_REFUND}'))
async def handle_refund_choise(event: CallbackQuery, lang: Language,
                               state: FSMContext, bot: Bot):
    await state.set_state(ExchangeForm.rate_type)
    await bot.send_message(
        chat_id=event.from_user.id,
        text='HI'
    )