import logging

from src.models import Transaction, TransactionStatuses

logger = logging.getLogger(__name__)


class TransactionNotifier:

    def __init__(self, bot) -> None:
        self.bot = bot

    async def notify(self, transaction: Transaction) -> None:
        try:
            chat_id = transaction.user.tg_id
            if not chat_id:
                logger.warning(f'No chat_id found for transaction {transaction.id}')
                return

            message = self._generate_message(transaction)
            if not message:
                logger.warning(f'No message generated for transaction {transaction.id}')
                return

            await self.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f'Notification sent for transaction {transaction.id} to chat {chat_id}')
        except Exception as e:
            logger.error(f'Failed to send notification for transaction {transaction.id}: {e}', exc_info=True)
            raise

    def _generate_message(self, transaction: Transaction) -> str:
        status_messages = {
            TransactionStatuses.NEW: f'🚀 Новая транзакция создана: {transaction.id}.',
            TransactionStatuses.PENDING: f'⌛ Транзакция {transaction.id} ожидает обработки.',
            TransactionStatuses.EXCHANGE: f'🔄 Транзакция {transaction.id} находится в процессе обмена.',
            TransactionStatuses.WITHDRAW: f'💸 Транзакция {transaction.id} выполняет вывод средств.',
            TransactionStatuses.DONE: f'✅ Транзакция {transaction.id} успешно завершена!',
            TransactionStatuses.EXPIRED: f'⏳ Транзакция {transaction.id} истекла.',
            TransactionStatuses.EMERGENCY: f'⚠️ Экстренная ситуация с транзакцией {transaction.id}.'
        }

        return status_messages.get(transaction.status, f'Статус транзакции {transaction.id}: {transaction.status}.')
