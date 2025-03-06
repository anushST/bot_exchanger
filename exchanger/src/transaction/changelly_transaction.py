# flake8: noqa
import asyncio
import logging
from datetime import datetime

from sqlalchemy.future import select

from . import transaction_codes as tc
from src import exceptions as ex
from src.api import exceptions as api_ex
from src.api.changelly import schemas
from src.api.changelly import changelly_client
from src.api.coin_redis_data import coin_redis_data_client
from src.enums import Exchangers
from src.core.db import get_session
from src.models import (
    DirectionTypes, Transaction, TransactionStatuses, RateTypes)

logger = logging.getLogger(__name__)


class ChangellyTransaction:

    def __init__(self, transaction_id: str) -> None:
        self.transaction_id = transaction_id

    async def process(self) -> None:
        logger.debug('Handled by changelly')
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
                    Exchangers.CHANGELLY,
                    transaction.from_currency,
                    network=transaction.from_currency_network
                )
                toCcy = await coin_redis_data_client.get_coin_full_info(
                    Exchangers.CHANGELLY,
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
                if transaction.rate_type == RateTypes.FIXED:
                    amount_from = None
                    amount_to = None
                    if transaction.direction == DirectionTypes.FROM.value:
                        amount_from = str(transaction.amount)
                    elif transaction.direction == DirectionTypes.TO.value:
                        amount_to = str(transaction.amount)
                    data = schemas.CreateFixedTransaction(
                        from_=fromCcy.code,
                        to=toCcy.code,
                        rateId='CipherSwap',
                        address=transaction.to_address,
                        amount_from=amount_from,
                        amount_to=amount_to,
                        extraId=transaction.tag_value,
                        refundAddress=transaction.refund_address,
                        refundExtraId=transaction.refund_tag_value
                    )
                else:
                    data = schemas.CreateFloatTransaction(
                        from_=fromCcy.code,
                        to=toCcy.code,
                        address=transaction.to_address,
                        extraId=transaction.tag_value,
                        amountFrom=str(transaction.amount),
                    )
                response = await changelly_client.create_float_transaction(
                    data
                )
                logger.info(response)
            except api_ex.InvalidAddressError:
                error_status_code = tc.INVALID_ADDRESS_CODE
            except api_ex.OutOFLimitisError:
                error_status_code = tc.OUT_OF_LIMITS_CODE
            except Exception as e:
                logger.error('Error Changelly client during order creation '
                             f'for transaction {self.transaction_id}: {e}',
                             exc_info=True)
                error_status_code = tc.UNDEFINED_ERROR_CODE
                raise
            try:
                async with get_session() as session:
                    transaction.exchanger = Exchangers.CHANGELLY.value
                    if error_status_code:
                        transaction.status = TransactionStatuses.ERROR.value
                        transaction.status_code = error_status_code
                    elif (response.currency_from != fromCcy.code
                          and response.currency_to != toCcy.code):
                        transaction.status = TransactionStatuses.ERROR.value
                        transaction.status_code = tc.UNDEFINED_ERROR_CODE
                    else:
                        transaction.status = TransactionStatuses.CREATED.value
                        transaction.status_code = tc.CREATED
                        transaction.exchanger = Exchangers.CHANGELLY.value
                        transaction.transaction_id = response.id_
                        transaction.transaction_token = ''

                        transaction.final_rate_type = response.type_
                        transaction.time_registred = datetime.fromtimestamp(response.created_at / 1_000_000) # noqa

                        # Final from
                        transaction.final_from_currency = transaction.from_currency # noqa
                        transaction.final_from_network = transaction.from_currency_network# noqa
                        transaction.final_from_amount = response.amount_expected_from # noqa
                        transaction.final_from_address = response.payin_address # noqa
                        transaction.final_from_tag_name = 'Memo/Comment/ID' if response.payin_extra_id else None # noqa
                        transaction.final_from_tag_value = response.payin_extra_id # noqa

                        # Final to
                        transaction.final_to_currency = transaction.to_currency
                        transaction.final_to_network = transaction.to_currency_network # noqa
                        transaction.final_to_amount = response.amount_expected_to # noqa
                        transaction.final_to_address = response.payout_address
                        transaction.final_to_tag_name = 'Memo/Comment/ID' if response.payout_extra_id else None # noqa
                        transaction.final_to_tag_value = response.payout_extra_id # noqa

                        # Final back
                        if response.type_ != RateTypes.FLOAT.value:
                            transaction.final_back_currency = transaction.from_currency # noqa
                            transaction.final_back_network = transaction.from_currency_network # 
                            transaction.final_back_amount = response.amount_expected_from
                            transaction.final_back_address = response.refund_address # noqa
                            transaction.final_back_tag_name = 'Memo/Comment/ID' if response.refund_extra_id else None # noqa
                            transaction.final_back_tag_value = response.refund_extra_id # noqa
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

    @staticmethod
    async def observer_process() -> None:
        logger.info('Changelly processor started')
        while True:
            try:
                async with get_session() as session:
                    result = await session.execute(
                        select(Transaction)
                        .where(Transaction.exchanger == Exchangers.CHANGELLY.value)
                        .where(~Transaction.status.in_([
                            TransactionStatuses.NEW.value,
                            TransactionStatuses.ERROR.value,
                            TransactionStatuses.HANDLED.value,
                            TransactionStatuses.DONE.value
                        ]))
                    )
                    transactions = result.scalars().all()
            except Exception as e:
                logger.error(f'Error occured')
                raise ex.DatabaseError(
                    'Error accessing transaction database') from e

            ids = [tr.transaction_id for tr in transactions]

            responses: list[schemas.TransactionDetails] = []
            for i in range(0, len(ids), 50):
                batch_ids = ids[i:i+50]
                response = await changelly_client.get_transaction_details(
                    schemas.CreateTransactionDetails(id=batch_ids, limit=60)
                )
                responses.extend(response)

            for response in responses:
                try:
                    async with get_session() as session:
                        result = await session.execute(
                            select(Transaction)
                            .where(Transaction.transaction_id == response.id_)
                            .where(Transaction.exchanger == Exchangers.CHANGELLY.value) # noqa
                        )
                        transaction = result.scalars().first()
                    if not response:
                        logger.error('No such transaction')
                        return

                    status_mapping = {
                        schemas.ChangellyStatuses.WAITING: TransactionStatuses.CREATED.value, # noqa
                        schemas.ChangellyStatuses.CONFIRMING: TransactionStatuses.PENDING.value, # noqa
                        schemas.ChangellyStatuses.EXCHANGING: TransactionStatuses.EXCHANGE.value, # noqa
                        schemas.ChangellyStatuses.SENDING: TransactionStatuses.WITHDRAW.value, # noqa
                        schemas.ChangellyStatuses.FINISHED: TransactionStatuses.DONE.value, # noqa
                        schemas.ChangellyStatuses.EXPIRED: TransactionStatuses.EXPIRED.value, # noqa
                        schemas.ChangellyStatuses.FAILED: TransactionStatuses.EMERGENCY.value, # noqa
                        schemas.ChangellyStatuses.HOLD: TransactionStatuses.EMERGENCY.value, # noqa
                        schemas.ChangellyStatuses.OVERDUE: TransactionStatuses.EMERGENCY.value, # noqa
                    }

                    new_status = status_mapping.get(schemas.ChangellyStatuses(response.status))
                    if new_status is None:
                        logger.error('Unknown status retrieved for transaction '
                                     f'{transaction.id}: {response.status}')
                        raise ValueError('Unknown ransaction status received')

                    try:
                        async with get_session() as session:
                            if new_status != transaction.status:
                                transaction.status = new_status
                                logger.info(f'Transaction {transaction.id} updated to ' # noqa
                                            f'status {new_status}.')
                            # from
                            transaction.received_from_id = response.payin_hash
                            transaction.received_from_amount = response.amount_from# noqa
                            transaction.received_from_confirmations = response.payin_confirmations # noqa
                            # to
                            transaction.received_to_id = response.payout_hash
                            transaction.received_to_amount = response.amount_to # noqa
                            transaction.received_to_confirmations = 0 # noqa
                            # back
                            transaction.received_back_id = response.refund_hash

                            session.add(transaction)
                            await session.commit()
                            await session.refresh(transaction)
                    except Exception as e:
                        raise ex.DatabaseError(
                            'Error accessing transaction database') from e
                except Exception as e:
                    logger.error('Error handling HANDLED transaction', exc_info=True)
                    raise
            await asyncio.sleep(10)
