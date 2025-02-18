import asyncio
import logging
from datetime import datetime

from sqlalchemy.future import select

from src import exceptions as ex
from src.api import exceptions as api_ex
from src.api.easybit import schemas, easybit_client
from src.database import get_session
from src.models import Transaction, TransactionStatuses

logger = logging.getLogger(__name__)

class EasyBitTransaction:
    def __init__(self, transaction_id: str) -> None:
        self.transaction_id = transaction_id

    async def process(self) -> None:
        try:
            sleep_time = 5
            while True:
                transaction = await self._get_transaction()
                if not transaction:
                    logger.warning(f"Transaction {self.transaction_id} not found.")
                    break

                # Если статус NEW - запускаем обработку, иначе переходим в handled
                if transaction.status == TransactionStatuses.NEW.value:
                    await self._handle_new(transaction)
                else:
                    await self._handle_handled(transaction)

                if transaction.status in (TransactionStatuses.DONE.value,
                                          TransactionStatuses.ERROR.value,
                                          TransactionStatuses.EXPIRED.value,
                                          TransactionStatuses.EMERGENCY.value):
                    logger.info(f"Transaction {self.transaction_id} reached final status: {transaction.status}")
                    break

                await asyncio.sleep(sleep_time)
        except Exception as e:
            logger.critical(f"Unhandled exception in processing transaction {self.transaction_id}: {e}", exc_info=True)
            async with get_session() as session:
                transaction = await self._get_transaction()
                if transaction:
                    transaction.status = TransactionStatuses.ERROR.value
                    session.add(transaction)
                    await session.commit()

    async def _get_transaction(self) -> Transaction | None:
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(Transaction).where(Transaction.id == self.transaction_id)
                )
                return result.scalars().first()
        except Exception as e:
            logger.error(f"Error retrieving transaction {self.transaction_id}: {e}", exc_info=True)
            raise ex.DatabaseError("Error accessing transaction database") from e

    async def _handle_new(self, transaction: Transaction) -> None:
        try:
            # Формируем данные для создания транзакции через EasyBit API
            order_data = schemas.CreateOrder(
                type=transaction.rate_type,
                fromCcy=transaction.from_currency,
                toCcy=transaction.to_currency,
                direction=transaction.direction,
                amount=transaction.amount,
                toAddress=transaction.to_address,
                tag=transaction.tag_value
            )
            try:
                response = await easybit_client.create_order(order_data)
                logger.info(f"EasyBit order created: {response}")
            except api_ex.InvalidAddressError:
                transaction.status = TransactionStatuses.ERROR.value
                logger.error(f"Invalid address for transaction {self.transaction_id}")
                return
            except Exception as e:
                logger.error(f"Error creating order for transaction {self.transaction_id}: {e}", exc_info=True)
                transaction.status = TransactionStatuses.ERROR.value
                return

            async with get_session() as session:
                # Обновляем статус и данные транзакции на основе ответа EasyBit
                transaction.status = TransactionStatuses.CREATED.value
                transaction.transaction_id = response.id
                transaction.transaction_token = response.token
                transaction.time_registred = datetime.fromtimestamp(response.time.reg)
                transaction.time_expiration = datetime.fromtimestamp(response.time.expiration)
                # Дополнительное обновление информации о валютах, если требуется
                session.add(transaction)
                await session.commit()

            logger.info(f"Transaction {self.transaction_id} successfully handled as NEW.")
        except Exception as e:
            logger.error(f"Error handling NEW transaction {self.transaction_id}: {e}", exc_info=True)
            raise

    async def _handle_handled(self, transaction: Transaction) -> None:
        try:
            # Получаем статус заказа
            details = {"id": transaction.transaction_id, "token": transaction.transaction_token}
            try:
                status_response = await easybit_client.get_order_status(transaction.transaction_id)
                logger.info(f"Order status for transaction {self.transaction_id}: {status_response}")
            except Exception as e:
                logger.error(f"Error fetching order status for transaction {self.transaction_id}: {e}", exc_info=True)
                return

            status_mapping = {
                "new": TransactionStatuses.CREATED.value,
                "pending": TransactionStatuses.PENDING.value,
                "exchange": TransactionStatuses.EXCHANGE.value,
                "withdraw": TransactionStatuses.WITHDRAW.value,
                "done": TransactionStatuses.DONE.value,
                "expired": TransactionStatuses.EXPIRED.value,
                "emergency": TransactionStatuses.EMERGENCY.value,
            }
            new_status = status_mapping.get(status_response.get("status"))
            if not new_status:
                logger.error(f"Unknown status for transaction {self.transaction_id}: {status_response.get('status')}")
                raise ValueError("Unknown transaction status received")

            async with get_session() as session:
                if new_status != transaction.status:
                    transaction.status = new_status
                    logger.info(f"Transaction {self.transaction_id} updated to status {new_status}.")
                session.add(transaction)
                await session.commit()
                await session.refresh(transaction)
        except Exception as e:
            logger.error(f"Error handling transaction {self.transaction_id}: {e}", exc_info=True)
            raise
