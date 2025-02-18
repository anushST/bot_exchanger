import asyncio
import logging

from . import transaction_codes as tc
from .ffio_transaction import FFioTransaction
from .changelly_transaction import ChangellyTransaction
from .easybit_transaction import EasyBitTransaction
from src.api import rate_data
from src.database import get_session
from src.enums import Exchangers
from src.models import RateTypes, Transaction, TransactionStatuses

logger = logging.getLogger(__name__)


class TransactionDispatcher:
    """Dispatch transaction to a exchanger."""

    transaction_mapping = {
        Exchangers.CHANGELLY.value: ChangellyTransaction,
        Exchangers.FFIO.value: FFioTransaction,
        Exchangers.EASYBIT.value: EasyBitTransaction
    }

    def __init__(self) -> None:
        """Start here the Transaction Processor's loop."""
        asyncio.create_task(ChangellyTransaction.observer_process())

    async def get_best_exchanger(self, transaction: Transaction) -> None:
        if transaction.status == TransactionStatuses.HANDLED.value:
            if transaction.rate_type == RateTypes.FIXED.value:
                rate_data_obj = await rate_data.get_fixed_best_rate(
                    from_coin=transaction.from_currency,
                    from_coin_network=transaction.from_currency_network,
                    to_coin=transaction.to_currency,
                    to_coin_network=transaction.to_currency_network
                )
                if rate_data_obj:
                    return self.transaction_mapping[
                        rate_data_obj[0]](transaction.id)
            else:
                rate_data_obj = await rate_data.get_float_best_rate(
                    from_coin=transaction.from_currency,
                    from_coin_network=transaction.from_currency_network,
                    to_coin=transaction.to_currency,
                    to_coin_network=transaction.to_currency_network
                )
                if rate_data_obj:
                    return self.transaction_mapping[
                        rate_data_obj[0]](transaction.id)
            return
        raise ValueError('In dispatcher the transaction status '
                         'should be always new')

    async def add(self, transaction: Transaction) -> None:
        best_exchanger = await self.get_best_exchanger(transaction)
        if best_exchanger:
            asyncio.create_task(best_exchanger.process())
            return
        async with get_session() as session:
            transaction.status = TransactionStatuses.ERROR.value
            transaction.status_code = tc.UNDEFINED_ERROR_CODE
            session.add(transaction)
            await session.commit()
