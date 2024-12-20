import asyncio
import logging

from src.models import Transaction, TransactionStatuses
from .ffio_transaction import FFioTransaction

logger = logging.getLogger(__name__)


class TransactionDispatcher:
    """Dispatch transaction to a exchanger."""

    async def get_best_exchanger(self, transaction: Transaction) -> None:
        if transaction.status == TransactionStatuses.HANDLED:
            asyncio.create_task(FFioTransaction(transaction.id).process())
            return
        raise ValueError('In dispatcher the transaction status '
                         'should be always new')

    async def add(self, transaction: Transaction) -> None:
        await self.get_best_exchanger(transaction)
