import asyncio
import logging

from sqlalchemy.future import select

from . import transaction_codes as tc
from src import exceptions as ex
from src.api import exceptions as api_ex
from src.api.ffio import schemas
from src.api.ffio.ffio_client import ffio_client
from src.api.ffio.ffio_redis_data import ffio_redis_client
from src.database import get_session
from src.models import Transaction, TransactionStatuses

logger = logging.getLogger(__name__)


class FFioTransaction:

    def __init__(self, transaction_id: str) -> None:
        self.transaction_id = transaction_id

    async def process(self) -> None:
        logger.info('Handled by ffio')
        try:
            while True:
                try:
                    transaction = await self._get_transaction()
                except ex.DatabaseError as e:
                    logger.error('Database error while fetching transaction '
                                 f'{self.transaction_id}: {e}', exc_info=True)
                    break

                if not transaction:
                    logger.warning(
                        f'Transaction {self.transaction_id} not found.')
                    break

                if transaction.status == TransactionStatuses.NEW:
                    logger.error('Invalid transaction status NEW '
                                 f'for {self.transaction_id}')
                    break

                stop_processing_statuses = (
                    TransactionStatuses.DONE,
                    TransactionStatuses.ERROR,
                    TransactionStatuses.EXPIRED,
                )
                if transaction.status in stop_processing_statuses:
                    logger.info('Stopping processing for transaction '
                                f'{self.transaction_id} with status '
                                f'{transaction.status}')
                    break

                try:
                    if transaction.status == TransactionStatuses.HANDLED:
                        await self._handle_new(transaction)
                    else:
                        await self._handle_handled(transaction)
                except Exception as e:
                    logger.error(f'Error during transaction processing '
                                 f'{self.transaction_id}: {e}', exc_info=True)
                    break

                await asyncio.sleep(5)
        except Exception as e:
            logger.critical('Unhandled exception in transaction processing '
                            f'{self.transaction_id}: {e}', exc_info=True)
            raise

    async def _get_transaction(self) -> Transaction | None:
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(Transaction).where(
                        Transaction.id == self.transaction_id)
                )
                return result.scalars().first()
        except Exception as e:
            logger.error(f'Error retrieving transaction {self.transaction_id} '
                         f'from database: {e}', exc_info=True)
            raise ex.DatabaseError(
                'Error accessing transaction database') from e

    async def _handle_new(self, transaction: Transaction) -> None:
        try:
            try:
                fromCcy = await ffio_redis_client.get_coin_full_info(
                    transaction.from_currency,
                    network=transaction.from_currency_network
                )
                toCcy = await ffio_redis_client.get_coin_full_info(
                    transaction.to_currency,
                    network=transaction.to_currency_network
                )
            except ex.RedisError as e:
                logger.error('Redis error while fetching currency info '
                             f'for transaction {transaction.id}: {e}',
                             exc_info=True)
                raise

            data = schemas.CreateOrder(
                type=transaction.rate_type,
                fromCcy=fromCcy.code,
                toCcy=toCcy.code,
                direction=transaction.direction,
                amount=transaction.amount,
                toAddress=transaction.to_address
            )

            try:
                response = await ffio_client.create(data)
            except api_ex.InvalidAddressError:
                status_code = tc.INVALID_ADDRESS_CODE
            except api_ex.IncorrectDirectionError:
                status_code = tc.INCORRECT_DIRECTION_CODE
            except api_ex.OutOFLimitisError:
                status_code = tc.OUT_OF_LIMITIS_CODE
            except api_ex.PartnerInternalError:
                status_code = tc.PARTNET_INTERNAL_ERROR_CODE
            except ex.ClientError as e:
                logger.error('Error from FFIO client during order creation '
                             f'for transaction {transaction.id}: {e}',
                             exc_info=True)
                raise

            if not response:
                logger.error('Empty response from FFIO client for '
                             f'transaction {transaction.id}')
                return
            try:
                async with get_session() as session:
                    if status_code:
                        transaction.status = TransactionStatuses.ERROR
                        transaction.is_status_showed = False
                        transaction.status_code = status_code
                    else:
                        transaction.transaction_id = response.id
                        transaction.transaction_token = response.token
                        transaction.status = TransactionStatuses.CREATED
                        transaction.is_status_showed = False
                        transaction.final_from_amount = response.from_info.amount # noqa
                        transaction.final_to_amount = response.to_info.amount
                        transaction.address_to_send_amount = response.from_info.address # noqa
                    session.add(transaction)
                    await session.commit()
                    await session.refresh(transaction)
            except Exception as e:
                logger.error('Error retrieving transaction '
                             f'{self.transaction_id} '
                             f'from database: {e}', exc_info=True)
                raise ex.DatabaseError(
                    'Error accessing transaction database') from e

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

            try:
                response = await ffio_client.order(data)
            except ex.ClientError as e:
                logger.error('Error from FFIO client during order retrieval '
                             f'for transaction {transaction.id}: {e}',
                             exc_info=True)
                raise

            if not response:
                logger.error('Empty response from FFIO client for '
                             f'transaction {transaction.id}')
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
            if new_status is None:
                logger.error('Unknown status retrieved for transaction '
                             f'{transaction.id}: {response.status}')
                raise ValueError('Unknown transaction status received')

            try:
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
                logger.error(f'Error retrieving transaction '
                             f'{self.transaction_id} '
                             f'from database: {e}', exc_info=True)
                raise ex.DatabaseError(
                    'Error accessing transaction database') from e

        except Exception as e:
            logger.error('Error handling HANDLED transaction '
                         f'{transaction.id}: {e}', exc_info=True)
            raise
