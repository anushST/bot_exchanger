import asyncio
import logging

from sqlalchemy.future import select

from src.api.ffio import schemas
from src.api.ffio.ffio_client import ffio_client
from src.models import Transaction, TransactionStatuses
from src.database import get_session

logger = logging.getLogger(__name__)


class FFioTransaction:

    def __init__(self, transaction_id: str) -> None:
        self.transaction_id = transaction_id

    async def process(self) -> None:
        logger.info('Handled by ffio')
        breakpoint()
        try:
            while True:
                transaction = await self._get_transaction()
                if not transaction:
                    logger.warning(
                        f'Transaction {self.transaction_id} not found.')
                    break

                if transaction.status == TransactionStatuses.NEW:
                    raise Exception('Incorrect status for the transaction '
                                    'in a processor NEW')

                stop_processing_statuses = (TransactionStatuses.DONE,
                                            TransactionStatuses.ERROR,
                                            TransactionStatuses.EXPIRED,)
                if transaction.status in stop_processing_statuses:
                    break

                if transaction.status == TransactionStatuses.HANDLED:
                    await self._handle_new(transaction)
                else:
                    await self._handle_handled(transaction)
                await asyncio.sleep(5)
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
                transaction.transaction_id = response.id
                transaction.transaction_token = response.token
                transaction.status = TransactionStatuses.CREATED
                transaction.is_status_showed = False
                transaction.final_from_amount = response.from_info.amount
                transaction.final_to_amount = response.to_info.amount
                transaction.address_to_send_amount = response.from_info.address
                session.add(transaction)
                await session.commit()
                await session.refresh(transaction)

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
            response = await ffio_client.order(data)
            if not response:
                logger.error('Failed to retrieve order details '
                             f'for transaction {transaction.id}.')
                return

            status_mapping = {
                schemas.OrderStatus.NEW: TransactionStatuses.CREATED,
                schemas.OrderStatus.PENDING: TransactionStatuses.PENDING,
                schemas.OrderStatus.EXCHANGE: TransactionStatuses.EXCHANGE,
                schemas.OrderStatus.WITHDRAW: TransactionStatuses.WITHDRAW,
                schemas.OrderStatus.DONE: TransactionStatuses.DONE,
                schemas.OrderStatus.EXPIRED: TransactionStatuses.EXPIRED,
                schemas.OrderStatus.EMERGENCY: TransactionStatuses.EMERGENCY,
            }

            new_status = status_mapping.get(response.status)
            logger.info(f'Status of the transaction: {new_status}')
            if new_status is None:
                raise ValueError('Unknown status retrieved: '
                                 f'{response.status}')
            if new_status != transaction.status:
                async with get_session() as session:
                    transaction.status = new_status
                    transaction.is_status_showed = False
                    session.add(transaction)
                    await session.commit()
                    await session.refresh(transaction)

                logger.info(f'Transaction {transaction.id} updated to '
                            f'status {new_status}.')
        except Exception as e:
            logger.error('Error handling HANDLED transaction '
                         f'{transaction.id}: {e}', exc_info=True)
            raise
