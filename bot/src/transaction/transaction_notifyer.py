import logging

from src.models import Transaction, TransactionStatuses, RateTypes
from src.utils import format_message

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
        except Exception as e:
            logger.error('Failed to send notification for transaction '
                         f'{transaction.id}: {e}', exc_info=True)
            raise

    def _generate_message(self, transaction: Transaction) -> str:
        lang = transaction.user.get_lang()
        if transaction.rate_type == RateTypes.FIXED:
            created_text = lang.transaction.created_fixed
        elif transaction.rate_type == RateTypes.FLOAT:
            created_text = lang.transaction.created_float
        else:
            raise Exception('No such rate_type')

        status_messages = {
            TransactionStatuses.CREATED: created_text,
            TransactionStatuses.PENDING: lang.transaction.pending,
            TransactionStatuses.EXCHANGE: lang.transaction.exchange,
            TransactionStatuses.WITHDRAW: lang.transaction.withdraw,
            TransactionStatuses.DONE: lang.transaction.done,
            TransactionStatuses.EXPIRED: lang.transaction.expired,
            TransactionStatuses.EMERGENCY: lang.transaction.emergency,
        }
        message = status_messages.get(transaction.status)
        if message:
            return format_message(message, **transaction.to_dict())
