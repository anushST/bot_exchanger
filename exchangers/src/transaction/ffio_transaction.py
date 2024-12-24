import asyncio
import logging
from datetime import datetime

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
                             f'for transaction {self.transaction_id}: {e}',
                             exc_info=True)
                raise

            data = schemas.CreateOrder(
                type=transaction.rate_type,
                fromCcy=fromCcy.code,
                toCcy=toCcy.code,
                direction=transaction.direction,
                amount=transaction.amount,
                toAddress=transaction.to_address,
                tag=transaction.tag_value
            )

            response = None
            error_status_code = None
            try:
                response = await ffio_client.create(data)
            except api_ex.InvalidAddressError:
                error_status_code = tc.INVALID_ADDRESS_CODE
            except api_ex.OutOFLimitisError:
                error_status_code = tc.OUT_OF_LIMITS_CODE
            except ex.ClientError as e:
                logger.error('Error from FFIO client during order creation '
                             f'for transaction {self.transaction_id}: {e}',
                             exc_info=True)
                raise
            try:
                async with get_session() as session:
                    if error_status_code:
                        transaction.status = TransactionStatuses.ERROR
                        transaction.is_status_showed = False
                        transaction.status_code = error_status_code
                    else:
                        transaction.status = TransactionStatuses.CREATED
                        transaction.is_status_showed = False

                        transaction.transaction_id = response.id
                        transaction.transaction_token = response.token
                        transaction.final_rate_type = response.type.value
                        transaction.time_registred = datetime.fromtimestamp(response.time.reg) # noqa
                        transaction.time_expiration = datetime.fromtimestamp(response.time.expiration) # noqa

                        # Final from
                        transaction.final_from_currency = response.from_info.coin # noqa
                        transaction.final_from_network = response.from_info.network # noqa
                        transaction.final_from_amount = response.from_info.amount # noqa
                        transaction.final_from_address = response.from_info.address # noqa
                        transaction.final_from_tag_name = response.from_info.tag_name # noqa
                        transaction.final_from_tag_value = response.from_info.tag_value # noqa

                        # Final to
                        transaction.final_to_currency = response.to_info.coin
                        transaction.final_to_network = response.to_info.network
                        transaction.final_to_amount = response.to_info.amount
                        transaction.final_to_address = response.to_info.address
                        transaction.final_to_tag_name = response.to_info.tag_name # noqa
                        transaction.final_to_tag_value = response.to_info.tag_value # noqa
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
                f'Transaction {self.transaction_id} successfully '
                'handled as NEW.')
        except Exception as e:
            logger.error('Error handling NEW transaction '
                         f'{self.transaction_id}: {e}', exc_info=True)
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
                             f'for transaction {self.transaction_id}: {e}',
                             exc_info=True)
                raise

            if not response:
                logger.error('Empty response from FFIO client for '
                             f'transaction {self.transaction_id}')
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
                             f'{self.transaction_id}: {response.status}')
                raise ValueError('Unknown transaction status received')

            try:
                async with get_session() as session:
                    if new_status != transaction.status:
                        transaction.status = new_status
                        transaction.is_status_showed = False
                        logger.info(f'Transaction {self.transaction_id} updated to ' # noqa
                                    f'status {new_status}.')
                    # from
                    transaction.received_from_id = response.from_info.tx.id
                    transaction.received_from_amount = response.from_info.tx.amount # noqa
                    transaction.received_from_confirmations = response.from_info.tx.confirmations # noqa
                    # to
                    transaction.received_to_id = response.to_info.tx.id
                    transaction.received_to_amount = response.to_info.tx.amount # noqa
                    transaction.received_to_confirmations = response.to_info.tx.confirmations # noqa
                    # back
                    transaction.received_back_id = response.back_info.tx.id
                    transaction.received_back_amount = response.back_info.tx.amount # noqa
                    transaction.received_back_confirmations = response.back_info.tx.confirmations # noqa

                    session.add(transaction)
                    await session.commit()
                    await session.refresh(transaction)
            except Exception as e:
                logger.error(f'Error retrieving transaction '
                             f'{self.transaction_id} '
                             f'from database: {e}', exc_info=True)
                raise ex.DatabaseError(
                    'Error accessing transaction database') from e

        except Exception as e:
            logger.error('Error handling HANDLED transaction '
                         f'{self.transaction_id}: {e}', exc_info=True)
            raise
