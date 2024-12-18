import asyncio
import logging

from sqlalchemy.future import select

from src.api.ffio import schemas
from src.api.ffio.ffio_client import ffio_client
from src.models import Transaction, TransactionStatuses
from src.database import get_session

logger = logging.getLogger(__name__)


class FFioTransaction:

    def __init__(self, client, transaction_id: str) -> None:
        self.client = client
        self.transaction_id = transaction_id

    async def process(self) -> None:
        try:
            while True:
                transaction = await self._get_transaction()
                if not transaction:
                    logger.warning(
                        f'Transaction {self.transaction_id} not found.')
                    break

                stop_processing_statuses = (TransactionStatuses.DONE,
                                            TransactionStatuses.ERROR,
                                            TransactionStatuses.EXPIRED,)
                if transaction.status in stop_processing_statuses:
                    break

                if transaction.status == TransactionStatuses.NEW:
                    await self._handle_new(transaction)
                else:
                    await self._handle_handled(transaction)
                await asyncio.sleep(3)
        except Exception as e:
            logger.error('Error processing transaction '
                         f'{self.transaction_id}: {e}', exc_info=True)
            raise

    async def _get_transaction(self) -> Transaction | None:
        async with get_session() as session:
            result = await session.execute(
                select(Transaction).where(
                    Transaction.id == self.transaction_id)
            )
            return result.scalars().first()

    async def _handle_new(self, transaction: Transaction) -> None:
        try:
            data = schemas.CreateOrder(
                type=transaction.rate_type,
                fromCcy=transaction.from_currency,
                toCcy=transaction.to_currency,
                direction=transaction.direction,
                amount=transaction.amount,
                toAddress=transaction.to_address
            )
            response = await ffio_client.create(data)
            if not response:
                logger.error('Failed to create order for transaction '
                             f'{transaction.id}.', exc_info=True)
                return

            async with get_session() as session:
                transaction.id = response.id
                transaction.transaction_token = response.token
                transaction.status = TransactionStatuses.HANDLED
                session.add(transaction)
                await session.commit()

            logger.info(
                f'Transaction {transaction.id} successfully handled as NEW.')
        except Exception as e:
            logger.error('Error handling NEW transaction '
                         f'{transaction.id}: {e}', exc_info=True)
            raise

    async def _handle_handled(self, transaction: Transaction) -> None:
        try:
            data = schemas.CreateOrderDetails(
                id=transaction.transaction_id,
                token=transaction.transaction_token
            )
            response = await self.client.order(data)
            if not response:
                logger.error('Failed to retrieve order details '
                             f'for transaction {transaction.id}.')
                return

            status_mapping = {
                schemas.OrderStatus.NEW: TransactionStatuses.NEW,
                schemas.OrderStatus.PENDING: TransactionStatuses.PENDING,
                schemas.OrderStatus.EXCHANGE: TransactionStatuses.EXCHANGE,
                schemas.OrderStatus.WITHDRAW: TransactionStatuses.WITHDRAW,
                schemas.OrderStatus.DONE: TransactionStatuses.DONE,
                schemas.OrderStatus.EXPIRED: TransactionStatuses.EXPIRED,
                schemas.OrderStatus.EMERGENCY: TransactionStatuses.EMERGENCY,
            }

            new_status = status_mapping.get(response.status)
            if new_status is None:
                raise ValueError('Unknown status retrieved: '
                                 f'{response.status}')

            async with get_session() as session:
                transaction.status = new_status
                session.add(transaction)
                await session.commit()

            logger.info(f'Transaction {transaction.id} updated to '
                        f'status {new_status}.')
        except Exception as e:
            logger.error('Error handling HANDLED transaction '
                         f'{transaction.id}: {e}', exc_info=True)
            raise
