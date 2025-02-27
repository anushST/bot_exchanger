import asyncio
import logging
from src.enums import Exchangers
from datetime import datetime
from sqlalchemy.future import select
from src import exceptions as ex
from src.api.easybit import easybit_client, schemas as easybit_schemas
from src.api.coin_redis_data import coin_redis_data_client
from src.database import get_session
from src.models import Transaction, TransactionStatuses

logger = logging.getLogger(__name__)

class EasyBitTransaction:
    def __init__(self, transaction_id: str) -> None:
        self.transaction_id = transaction_id

    async def process(self) -> None:
        logger.info(f'Transaction {self.transaction_id} handled by EasyBit.')
        sleep_time = 5
        expired_retries = 0
        while expired_retries < 60 * 24:
            try:
                transaction = await self._get_transaction()
                if not transaction:
                    raise ex.TransactionNotFoundError(f'Transaction {self.transaction_id} not found.')

                if transaction.status == TransactionStatuses.NEW.value:
                    raise ex.InvalidTransactionStatusError(
                        f'Invalid transaction status NEW for {self.transaction_id}'
                    )

                stop_processing_statuses = (TransactionStatuses.DONE.value, TransactionStatuses.ERROR.value)
                if transaction.status in stop_processing_statuses:
                    logger.info(f'Stopping processing for transaction {self.transaction_id} with status {transaction.status}')
                    break

                if transaction.status == TransactionStatuses.EXPIRED.value:
                    sleep_time = 60
                    expired_retries += 1

                if transaction.status == TransactionStatuses.HANDLED.value:
                    await self._handle_new(transaction)
                else:
                    await self._handle_handled(transaction)

            except ex.DatabaseError as e:
                logger.error(f'Database error while fetching transaction {self.transaction_id}: {e}', exc_info=True)
                break
            except ex.TransactionNotFoundError as e:
                logger.warning(str(e))
                break
            except ex.InvalidTransactionStatusError as e:
                logger.error(str(e))
                break
            except (ex.TransactionProcessingError, ex.APIError) as e:
                logger.error(f'Error during transaction processing {self.transaction_id}: {e}', exc_info=True)
                break
            except Exception as e:
                logger.error(f'Unexpected error in transaction {self.transaction_id}: {e}', exc_info=True)
                break

            await asyncio.sleep(sleep_time)

    async def _get_transaction(self) -> Transaction | None:
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(Transaction).where(Transaction.id == self.transaction_id)
                )
                return result.scalars().first()
        except Exception as e:
            logger.error(f'Error retrieving transaction {self.transaction_id} from database: {e}', exc_info=True)
            raise ex.DatabaseError(f'Error accessing transaction database: {e}') from e

    async def _handle_new(self, transaction: Transaction) -> None:
        try:
            from_coin_info = await coin_redis_data_client.get_coin_full_info(
                Exchangers.EASYBIT, transaction.from_currency, transaction.from_currency_network
            )
            to_coin_info = await coin_redis_data_client.get_coin_full_info(
                Exchangers.EASYBIT, transaction.to_currency, transaction.to_currency_network
            )
            if not from_coin_info or not to_coin_info:
                raise ex.CoinInfoNotFoundError(f'Coin info not found for {self.transaction_id}')

            data = easybit_schemas.CreateOrderRequest(
                send=from_coin_info.code,
                receive=to_coin_info.code,
                amount=float(transaction.amount),
                receive_address=transaction.to_address,
                send_network=transaction.from_currency_network,
                receive_network=transaction.to_currency_network,
                receive_tag=transaction.tag_value if hasattr(transaction, 'tag_value') else None,
                refund_address=transaction.refund_address if hasattr(transaction, 'refund_address') else None,
                refund_tag=transaction.refund_tag if hasattr(transaction, 'refund_tag') else None,
            )

            response = await easybit_client.create_order(data)
            async with get_session() as session:
                transaction.status = TransactionStatuses.CREATED.value
                transaction.exchanger = Exchangers.EASYBIT.value
                transaction.transaction_id = response.data.id
                transaction.final_from_address = response.data.send_address
                transaction.final_from_amount = response.data.send_amount
                transaction.final_to_amount = response.data.receive_amount
                transaction.send_tag = response.data.send_tag if response.data.send_tag else None
                transaction.receive_tag = response.data.receive_tag if response.data.receive_tag else None
                transaction.refund_address = response.data.refund_address if response.data.refund_address else None
                transaction.refund_tag = response.data.refund_tag if response.data.refund_tag else None
                session.add(transaction)
                await session.commit()
                await session.refresh(transaction)

            logger.info(f'Transaction {self.transaction_id} successfully handled as NEW.')
        except ex.CoinInfoNotFoundError as e:
            logger.error(str(e))
            async with get_session() as session:
                transaction.status = TransactionStatuses.ERROR.value
                transaction.status_code = "COIN_INFO_NOT_FOUND"
                session.add(transaction)
                await session.commit()
        except ex.OrderCreationError as e:
            logger.error(f'Failed to create order for transaction {self.transaction_id}: {e}', exc_info=True)
            async with get_session() as session:
                transaction.status = TransactionStatuses.ERROR.value
                transaction.status_code = "ORDER_CREATION_FAILED"
                session.add(transaction)
                await session.commit()
            raise ex.APIError(f'API error in creating order for {self.transaction_id}: {e}') from e
        except Exception as e:
            logger.error(f'Error handling NEW transaction {self.transaction_id}: {e}', exc_info=True)
            async with get_session() as session:
                transaction.status = TransactionStatuses.ERROR.value
                transaction.status_code = "API_ERROR"
                session.add(transaction)
                await session.commit()
            raise ex.APIError(f'API error in handling new transaction {self.transaction_id}: {e}') from e

    async def _handle_handled(self, transaction: Transaction) -> None:
        try:
            order_id = transaction.transaction_id
            response = await easybit_client.get_order_status(order_id)

            status_mapping = {
                easybit_schemas.OrderStatusEnum.AWAITING_DEPOSIT: TransactionStatuses.PENDING.value,
                easybit_schemas.OrderStatusEnum.CONFIRMING_DEPOSIT: TransactionStatuses.PENDING.value,
                easybit_schemas.OrderStatusEnum.EXCHANGING: TransactionStatuses.EXCHANGE.value,
                easybit_schemas.OrderStatusEnum.SENDING: TransactionStatuses.WITHDRAW.value,
                easybit_schemas.OrderStatusEnum.COMPLETE: TransactionStatuses.DONE.value,
                easybit_schemas.OrderStatusEnum.REFUND: TransactionStatuses.REFUND.value,
                easybit_schemas.OrderStatusEnum.FAILED: TransactionStatuses.ERROR.value,
                easybit_schemas.OrderStatusEnum.VOLATILITY_PROTECTION: TransactionStatuses.EMERGENCY.value,
                easybit_schemas.OrderStatusEnum.ACTION_REQUEST: TransactionStatuses.EMERGENCY.value,
                easybit_schemas.OrderStatusEnum.REQUEST_OVERDUE: TransactionStatuses.EXPIRED.value,
            }
            new_status = status_mapping.get(response.data.status)
            if new_status is None:
                raise ex.UnknownTransactionStatusError(
                    f'Unknown status retrieved for transaction {self.transaction_id}: {response.data.status}'
                )

            async with get_session() as session:
                if new_status != transaction.status:
                    transaction.status = new_status
                    logger.info(f'Transaction {self.transaction_id} updated to status {new_status}.')
                transaction.received_from_id = response.data.hash_in if response.data.hash_in else transaction.received_from_id
                transaction.received_to_id = response.data.hash_out if response.data.hash_out else transaction.received_to_id
                transaction.received_to_amount = response.data.receive_amount or transaction.received_to_amount
                session.add(transaction)
                await session.commit()
                await session.refresh(transaction)
        except ex.UnknownTransactionStatusError as e:
            logger.error(str(e))
            raise ex.TransactionProcessingError(f'Failed to process transaction {self.transaction_id} due to unknown status') from e
        except Exception as e:
            logger.error(f'Error handling HANDLED transaction {self.transaction_id}: {e}', exc_info=True)
            raise ex.TransactionProcessingError(f'Failed to process handled transaction {self.transaction_id}: {e}') from e