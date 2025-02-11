# flake8: noqa
import asyncio
import logging
from src.enums import Exchangers
from datetime import datetime

from sqlalchemy.future import select

from . import transaction_codes as tc
from src import exceptions as ex
from src.api import exceptions as api_ex
from src.api.ffio import schemas
from src.api.ffio.ffio_client import ffio_client
from src.api.coin_redis_data import coin_redis_data_client
from src.database import get_session
from src.models import (
    Transaction, TransactionStatuses)

logger = logging.getLogger(__name__)


class FFioTransaction:

    def __init__(self, transaction_id: str) -> None:
        self.transaction_id = transaction_id

    async def process(self) -> None:
        logger.info(f'Transaction {self.transaction_id} handled by ffio.')
        try:
            sleep_time = 5
            expired_retries = 0
            while expired_retries < 60*24:
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

                if transaction.status == TransactionStatuses.NEW.value:
                    logger.error('Invalid transaction status NEW '
                                 f'for {self.transaction_id}')
                    break

                stop_processing_statuses = (
                    TransactionStatuses.DONE.value,
                    TransactionStatuses.ERROR.value
                )
                if transaction.status in stop_processing_statuses:
                    logger.info('Stopping processing for transaction '
                                f'{self.transaction_id} with status '
                                f'{transaction.status}')
                    break

                if transaction.status == TransactionStatuses.EXPIRED.value:
                    sleep_time = 60
                    expired_retries += 1

                try:
                    if transaction.status == TransactionStatuses.HANDLED.value:
                        await self._handle_new(transaction)
                    else:
                        await self._handle_handled(transaction)
                except Exception as e:
                    logger.error(f'Error during transaction processing '
                                 f'{self.transaction_id}: {e}', exc_info=True)
                    break

                await asyncio.sleep(sleep_time)
        except Exception as e:
            logger.critical('Unhandled exception in transaction processing '
                            f'{self.transaction_id}: {e}', exc_info=True)
            async with get_session() as session:
                    transaction.status = TransactionStatuses.ERROR.value
                    transaction.status_code = tc.UNDEFINED_ERROR_CODE
                    session.add(transaction)
                    await session.commit()

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
                fromCcy = await coin_redis_data_client.get_coin_full_info(
                    Exchangers.FFIO,
                    transaction.from_currency,
                    network=transaction.from_currency_network
                )
                toCcy = await coin_redis_data_client.get_coin_full_info(
                    Exchangers.FFIO,
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
                logger.info(response)
            except api_ex.InvalidAddressError:
                error_status_code = tc.INVALID_ADDRESS_CODE
            except api_ex.OutOFLimitisError:
                error_status_code = tc.OUT_OF_LIMITS_CODE
            except Exception as e:
                logger.error('Error from FFIO client during order creation '
                             f'for transaction {self.transaction_id}: {e}',
                             exc_info=True)
                error_status_code = tc.UNDEFINED_ERROR_CODE
            try:
                async with get_session() as session:
                    if error_status_code:
                        transaction.status = TransactionStatuses.ERROR.value
                        transaction.status_code = error_status_code
                    else:
                        transaction.status = TransactionStatuses.CREATED.value
                        transaction.status_code = tc.CREATED

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

    # async def _handle_emergency(self) -> None:
    #     logger.info('Emergency for transaction')
    #     try:
    #         while True:
    #             try:
    #                 transaction = await self._get_transaction()
    #             except ex.DatabaseError as e:
    #                 logger.error('Database error while fetching transaction '
    #                              f'{self.transaction_id}: {e}', exc_info=True)
    #                 break

    #             if not transaction:
    #                 logger.warning(
    #                     f'Transaction {self.transaction_id} not found.')
    #                 break

    #             if transaction.status != TransactionStatuses.EMERGENCY:
    #                 logger.critical('This transaction is not emergency '
    #                                 f'({self.transaction_id})')
    #                 break
    #             try:
    #                 if transaction.emergency_choise is not None:
    #                     if transaction.emergency_choise == EmergencyChoices.EXCHANGE: # noqa
    #                         data = schemas.CreateEmergency(
    #                             id=transaction.transaction_id,
    #                             token=transaction.transaction_token,
    #                             choice=transaction.emergency_choise
    #                         )
    #                     elif transaction.emergency_choise == EmergencyChoices.REFUND: # noqa
    #                         data = schemas.CreateEmergency(
    #                             id=transaction.transaction_id,
    #                             token=transaction.transaction_token,
    #                             choice=transaction.emergency_choise,
    #                             address=transaction.emergency_address,
    #                             tag=transaction.emergency_tag_value
    #                         )
    #                     else:
    #                         raise Exception('No such choise')  # ToDo

    #                     is_error = False
    #                     try:
    #                         if transaction.made_emergency_action:
    #                             transaction.made_emergency_action = False
    #                             await ffio_client.emergency(data)
    #                         else:
    #                             is_error = True
    #                     except api_ex.InvalidAddressError:
    #                         transaction.is_status_showed = False
    #                         transaction.status_code = tc.INVALID_EMERGENCY_ADDRESS_CODE # noqa
    #                         is_error = True
    #                     except Exception as e:
    #                         logger.error('Error from FFIO client during order creation ' # noqa
    #                                      f'for transaction {self.transaction_id}: {e}', # noqa
    #                                      exc_info=True)
    #                         continue

    #                     try:
    #                         async with get_session() as session:
    #                             transaction.is_emergency_handled = True
    #                             session.add(transaction)
    #                             await session.commit()
    #                             await session.refresh(transaction)
    #                     except Exception as e:
    #                         logger.error(f'Error retrieving transaction {self.transaction_id} ' # noqa
    #                                      f'from database: {e}', exc_info=True)
    #                         raise ex.DatabaseError(
    #                             'Error accessing transaction database') from e
    #                     if not is_error:
    #                         return
    #             except Exception as e:
    #                 logger.error(f'Error during transaction processing '
    #                              f'{self.transaction_id}: {e}', exc_info=True)
    #                 break

    #             await asyncio.sleep(5)
    #     except Exception as e:
    #         logger.critical('Unhandled exception in transaction processing '
    #                         f'{self.transaction_id}: {e}', exc_info=True)
    #         raise

    async def _handle_handled(self, transaction: Transaction) -> None:
        try:
            data = schemas.CreateOrderDetails(
                id=transaction.transaction_id,
                token=transaction.transaction_token
            )

            try:
                response = await ffio_client.order(data)
                logger.info(response)
            except Exception as e:
                logger.error('Error from FFIO client during order retrieval '
                             f'for transaction {self.transaction_id}: {e}',
                             exc_info=True)
                return

            if not response:
                logger.error('Empty response from FFIO client for '
                             f'transaction {self.transaction_id}')
                return

            status_mapping = {
                schemas.OrderStatus.NEW: TransactionStatuses.CREATED.value,
                schemas.OrderStatus.PENDING: TransactionStatuses.PENDING.value,
                schemas.OrderStatus.EXCHANGE: TransactionStatuses.EXCHANGE.value,
                schemas.OrderStatus.WITHDRAW: TransactionStatuses.WITHDRAW.value,
                schemas.OrderStatus.DONE: TransactionStatuses.DONE.value,
                schemas.OrderStatus.EXPIRED: TransactionStatuses.EXPIRED.value,
                schemas.OrderStatus.EMERGENCY: TransactionStatuses.EMERGENCY.value,
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
                    transaction.final_back_currency = response.back_info.coin
                    transaction.final_back_network = response.back_info.network
                    transaction.final_back_address = response.back_info.address
                    transaction.final_back_tag_name = response.back_info.tag_name # noqa
                    transaction.final_back_tag_value = response.back_info.tag_value # noqa
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
            # if (new_status == TransactionStatuses.EMERGENCY
            #         and not transaction.is_emergency_handled):
            #     await self._handle_emergency()

        except Exception as e:
            logger.error('Error handling HANDLED transaction '
                         f'{self.transaction_id}: {e}', exc_info=True)
            raise
