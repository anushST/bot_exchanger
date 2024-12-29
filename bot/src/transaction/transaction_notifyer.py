import logging
from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from src.keyboards import emergency as emerg_kbs
from src.models import (EmergencyChoices, EmergencyStatuses, RateTypes,
                        Transaction, TransactionStatuses)
from src.utils import format_message
from src.utils.time import difference_in_minutes
from src.transaction import transaction_codes as tc

logger = logging.getLogger(__name__)


class TransactionNotifier:

    def __init__(self, bot) -> None:
        self.bot = bot

    async def notify(self, transaction: Transaction) -> None:
        try:
            chat_id = transaction.user.tg_id
            if not chat_id:
                logger.warning(
                    f'No chat_id found for transaction {transaction.id}')
                return

            message = self._generate_message(transaction)
            reply_markup = self._get_reply_markup(transaction)
            if message:
                await self.bot.send_message(chat_id=chat_id, text=message,
                                            reply_markup=reply_markup)
            else:
                logger.warning
                (f'Message generation failed for transaction {transaction.id}')
        except Exception as e:
            logger.error(
                'Failed to send notification for transaction '
                f'{transaction.id}: {e}',
                exc_info=True
            )
            raise

    def _get_error_message(self, lang, transaction: Transaction) -> str:
        status_code = transaction.status_code
        if status_code == tc.INVALID_ADDRESS_CODE:
            return lang.transaction.error.incorrect_address
        elif status_code == tc.OUT_OF_LIMITS_CODE:
            return lang.transaction.error.out_of_limits
        elif status_code == tc.UNDEFINED_ERROR_CODE:
            return lang.transaction.error.undefined
        return ''

    def _get_emergency_message(self, lang, transaction: Transaction) -> str:
        status_code = transaction.status_code
        message = lang.transaction.emergency.choice
        if status_code == tc.INVALID_EMERGENCY_ADDRESS_CODE:
            message = lang.transaction.error.incorrect_emergency_address
        return message

    def _get_transaction_done_message(
            self, lang, transaction: Transaction) -> str:
        message = lang.transaction.done
        if transaction.emergency_choise == EmergencyChoices.REFUND:
            message = lang.transaction.emergency.done
        return message

    def _get_reply_markup(
            self, transaction: Transaction
            ) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
        lang = transaction.user.get_lang()
        reply_markup = None
        if transaction.status == TransactionStatuses.EMERGENCY:
            if transaction.status_code == tc.INVALID_EMERGENCY_ADDRESS_CODE:
                reply_markup = emerg_kbs.get_again_address_kb(
                    lang, transaction.id)
            else:
                has_exchange = True
                if EmergencyStatuses.LIMIT in transaction.get_emergency_statuses(): # noqa
                    has_exchange = False
                reply_markup = emerg_kbs.get_emergency_choice_kb(
                    lang, transaction.id, has_exchange)
        return reply_markup

    def _generate_message(self, transaction: Transaction) -> str:
        lang = transaction.user.get_lang()
        rate_type = transaction.rate_type
        created_text = None

        if rate_type == RateTypes.FIXED:
            created_text = lang.transaction.created_fixed
        elif rate_type == RateTypes.FLOAT:
            created_text = lang.transaction.created_float
        else:
            error_msg = (f'No such rate_type: {rate_type} '
                         f'for transaction {transaction.id}')
            raise ValueError(error_msg)

        status_messages = {
            TransactionStatuses.CREATED: created_text,
            TransactionStatuses.PENDING: lang.transaction.pending,
            TransactionStatuses.EXCHANGE: lang.transaction.exchange,
            TransactionStatuses.WITHDRAW: lang.transaction.withdraw,
            TransactionStatuses.DONE: self._get_transaction_done_message(lang, transaction), # noqa
            TransactionStatuses.EXPIRED: lang.transaction.expired,
            TransactionStatuses.EMERGENCY: self._get_emergency_message(lang, transaction), # noqa
            TransactionStatuses.ERROR: self._get_error_message(lang, transaction)  # noqa
        }

        message = status_messages.get(transaction.status)
        tag_data_from = None
        if transaction.final_back_tag_name:
            tag_data_from = format_message(
                lang.transaction.tag_data,
                tag_name=transaction.final_from_tag_name,
                tag_value=transaction.final_from_tag_value)
        tag_data_to = None
        if transaction.final_back_tag_name:
            tag_data_to = format_message(
                lang.transaction.tag_data,
                tag_name=transaction.final_to_tag_name,
                tag_value=transaction.final_to_tag_value)
        expire_time_minute = None
        if transaction.time_expiration:
            expire_time_minute = difference_in_minutes(
                datetime.now(),
                transaction.time_expiration
            )

        if message:
            return format_message(
                message,
                tag_data_from=tag_data_from,
                tag_data_to=tag_data_to,
                expire_time_minute=expire_time_minute,
                **transaction.to_dict())
