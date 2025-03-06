import asyncio
import logging
from src.enums import Exchangers
from datetime import datetime
from sqlalchemy.future import select
from src import exceptions as ex
from src.api.easybit import easybit_client, schemas as easybit_schemas
from src.api.coin_redis_data import coin_redis_data_client
from src.core.db import get_session
from src.models import Transaction, TransactionStatuses
from . import transaction_codes as tc
from src.api import exceptions as api_ex
from src.models import DirectionTypes, RateTypes

logger = logging.getLogger(__name__)

class EasyBitTransaction:
    def __init__(self, transaction_id: str) -> None:
        self.transaction_id = transaction_id

    async def process(self) -> None:
        logger.debug('Handled by Easybit')
        try:
            try:
                transaction = await self._get_transaction(self.transaction_id)
            except ex.DatabaseError as e:
                logger.error('Database error while fetching transaction '
                             f'{self.transaction_id}: {e}', exc_info=True)

            if not transaction:
                logger.warning(
                    f'Transaction {self.transaction_id} not found.')

            if transaction.status == TransactionStatuses.NEW.value:
                logger.error('Invalid transaction status NEW '
                             f'for {self.transaction_id}')

            try:
                if transaction.status == TransactionStatuses.HANDLED.value:
                    await self._handle_new(transaction)
            except Exception as e:
                logger.error('Error during transaction processing '
                             f'{self.transaction_id}: {e}', exc_info=True)
        except Exception as e:
            logger.critical('Unhandled exception in transaction processing '
                            f'{self.transaction_id}: {e}', exc_info=True)
            raise

    async def _get_transaction(self, transaction_id) -> Transaction | None:
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(Transaction).where(
                        Transaction.id == transaction_id)
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
                fromCcy = await coin_redis_data_client.get_coin_full_info(
                    Exchangers.EASYBIT,
                    transaction.from_currency,
                    network=transaction.from_currency_network
                )
                toCcy = await coin_redis_data_client.get_coin_full_info(
                    Exchangers.EASYBIT,
                    transaction.to_currency,
                    network=transaction.to_currency_network
                )
            except ex.RedisError as e:
                logger.error('Redis error while fetching currency info '
                             f'for transaction {self.transaction_id}: {e}',
                             exc_info=True)
                raise

            if not fromCcy or not toCcy:
                async with get_session() as session:
                    transaction.status = TransactionStatuses.ERROR.value
                    transaction.status_code = tc.UNDEFINED_ERROR_CODE
                    session.add(transaction)
                    await session.commit()
                return

            response = None
            error_status_code = None
            try:
                amount_type = None
                if transaction.direction == DirectionTypes.FROM.value:
                    amount_type = "send"
                elif transaction.direction == DirectionTypes.TO.value:
                    amount_type = "receive"

                order_request = easybit_schemas.CreateOrderRequest(
                    send=fromCcy.code,
                    receive=toCcy.code,
                    amount=float(transaction.amount),
                    receiveAddress=transaction.to_address,
                    receiveTag=transaction.tag_value,
                    sendNetwork=transaction.from_currency_network,
                    receiveNetwork=transaction.to_currency_network,
                    amountType=amount_type,
                    refundAddress=transaction.refund_address,
                    refundTag=transaction.refund_tag_value
                )
                
                response = await easybit_client.create_order(order_request)
                logger.info(response)
            except api_ex.InvalidAddressError:
                error_status_code = tc.INVALID_ADDRESS_CODE
            except api_ex.ValidationApiError:
                error_status_code = tc.OUT_OF_LIMITS_CODE
            except Exception as e:
                logger.error('Error Easybit client during order creation '
                             f'for transaction {self.transaction_id}: {e}',
                             exc_info=True)
                error_status_code = tc.UNDEFINED_ERROR_CODE
                raise
            
            try:
                async with get_session() as session:
                    transaction.exchanger = Exchangers.EASYBIT.value
                    if error_status_code:
                        transaction.status = TransactionStatuses.ERROR.value
                        transaction.status_code = error_status_code
                    else:
                        transaction.status = TransactionStatuses.CREATED.value
                        transaction.status_code = tc.CREATED
                        transaction.exchanger = Exchangers.EASYBIT.value
                        transaction.transaction_id = response.data.id
                        transaction.transaction_token = ''
                        
                        transaction.final_rate_type = RateTypes.FLOAT.value
                        transaction.time_registred = datetime.fromtimestamp(response.data.created_at / 1000)

                        # Final from
                        transaction.final_from_currency = transaction.from_currency
                        transaction.final_from_network = transaction.from_currency_network
                        transaction.final_from_amount = response.data.send_amount
                        transaction.final_from_address = response.data.send_address
                        transaction.final_from_tag_name = 'Memo/Tag/ID' if response.data.send_tag else None
                        transaction.final_from_tag_value = response.data.send_tag

                        # Final to
                        transaction.final_to_currency = transaction.to_currency
                        transaction.final_to_network = transaction.to_currency_network
                        transaction.final_to_amount = response.data.receive_amount
                        transaction.final_to_address = response.data.receive_address
                        transaction.final_to_tag_name = 'Memo/Tag/ID' if response.data.receive_tag else None
                        transaction.final_to_tag_value = response.data.receive_tag

                        # Final back
                        transaction.final_back_currency = transaction.from_currency
                        transaction.final_back_network = transaction.from_currency_network
                        transaction.final_back_amount = response.data.send_amount
                        transaction.final_back_address = response.data.refund_address
                        transaction.final_back_tag_name = 'Memo/Tag/ID' if response.data.refund_tag else None
                        transaction.final_back_tag_value = response.data.refund_tag
                        
                    session.add(transaction)
                    await session.commit()
                    await session.refresh(transaction)
            except Exception as e:
                logger.error('Error updating transaction '
                             f'{self.transaction_id} '
                             f'in database: {e}', exc_info=True)
                raise ex.DatabaseError(
                    'Error accessing transaction database') from e

            logger.info(
                f'Transaction {self.transaction_id} successfully '
                'handled as NEW.')
        except Exception as e:
            logger.error('Error handling NEW transaction '
                         f'{self.transaction_id}: {e}', exc_info=True)
            raise

    @staticmethod
    async def observer_process() -> None:
        logger.info('Easybit processor started')
        while True:
            try:
                async with get_session() as session:
                    result = await session.execute(
                        select(Transaction)
                        .where(Transaction.exchanger == Exchangers.EASYBIT.value)
                        .where(~Transaction.status.in_([
                            TransactionStatuses.NEW.value,
                            TransactionStatuses.ERROR.value,
                            TransactionStatuses.HANDLED.value,
                            TransactionStatuses.DONE.value
                        ]))
                    )
                    transactions = result.scalars().all()

                if not transactions:
                    logger.info('No active transactions to process.')
                    await asyncio.sleep(10)
                    continue

                earliest_time = min(
                    t.time_registred for t in transactions if t.time_registred
                )
                date_from = int((earliest_time - timedelta(hours=1)).timestamp() * 1000)
                transaction_dict = {t.transaction_id: t for t in transactions if t.transaction_id}

                status_mapping = {
                    "AWAITING_DEPOSIT": TransactionStatuses.CREATED.value,
                    "CONFIRMING_DEPOSIT": TransactionStatuses.PENDING.value,
                    "EXCHANGING": TransactionStatuses.EXCHANGE.value,
                    "SENDING": TransactionStatuses.WITHDRAW.value,
                    "COMPLETE": TransactionStatuses.DONE.value,
                    "REFUND": TransactionStatuses.ERROR.value,
                    "FAILED": TransactionStatuses.EMERGENCY.value,
                    "VOLATILITY_PROTECTION": TransactionStatuses.EMERGENCY.value,
                    "ACTION_REQUEST": TransactionStatuses.EMERGENCY.value,
                    "REQUEST_OVERDUE": TransactionStatuses.EMERGENCY.value,
                }

                while True:
                    orders_response = await easybit_client.get_orders(
                        dateFrom=date_from,
                        limit=2000,
                        sortDirection="ASC"
                    )
                    orders = orders_response.data  

                    async with get_session() as session:
                        for order in orders:
                            transaction = transaction_dict.get(order.id)
                            if not transaction:
                                continue

                            new_status = status_mapping.get(order.status)
                            if new_status is None:
                                logger.error(f'Unknown status for transaction {transaction.id}: {order.status}')
                                continue

                            if new_status != transaction.status:
                                transaction.status = new_status
                                logger.info(f'Transaction {transaction.id} updated to status {new_status}.')

                            transaction.received_to_amount = order.receive_amount
                            transaction.received_from_id = order.hash_in
                            transaction.received_to_id = order.hash_out
                            if order.updated_at:
                                transaction.time_lastupdate = datetime.fromtimestamp(order.updated_at / 1000)

                            session.add(transaction)

                        await session.commit()
                        logger.info(f'Processed {len(orders)} orders.')

                    if len(orders) < 2000:
                        break

                    last_order_time = orders[-1].created_at  
                    date_from = last_order_time + 1

            except Exception as e:
                logger.error(f'Error in observer_process: {e}', exc_info=True)
                raise ex.DatabaseError('Error processing transactions') from e

            await asyncio.sleep(10)