import logging
from datetime import datetime

from src.models import Transaction, TransactionStatuses, RateTypes
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
            if message:
                await self.bot.send_message(chat_id=chat_id, text=message)
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
        elif status_code:
            error_msg = (f'Unknown error code: {status_code} '
                         f'for transaction {transaction.id}')
            raise ValueError(error_msg)

    def _difference_in_minutes(start_time: datetime,
                               end_time: datetime) -> int:
        """"""
        pass

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
            TransactionStatuses.DONE: lang.transaction.done,
            TransactionStatuses.EXPIRED: lang.transaction.expired,
            TransactionStatuses.EMERGENCY: lang.transaction.emergency,
            TransactionStatuses.ERROR: self._get_error_message(lang, transaction)  # noqa
        }

        message = status_messages.get(transaction.status)
        tag_data_from = format_message(
            lang.transaction.tag_data,
            tag_name=transaction.final_from_tag_name,
            tag_value=transaction.final_from_tag_value)
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
