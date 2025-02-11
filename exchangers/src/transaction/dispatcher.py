import asyncio
import logging

from src.models import Transaction, TransactionStatuses
from .ffio_transaction import FFioTransaction
from .changelly_transaction import ChangellyTransaction

logger = logging.getLogger(__name__)


class TransactionDispatcher:
    """Dispatch transaction to a exchanger."""

    def __init__(self) -> None:
        """Start here the Transaction Processor's loop."""
        asyncio.create_task(ChangellyTransaction.observer_process())

    async def get_best_exchanger(self, transaction: Transaction) -> None:
        if transaction.status == TransactionStatuses.HANDLED.value:
            # asyncio.create_task(FFioTransaction(transaction.id).process())
            asyncio.create_task(ChangellyTransaction(transaction.id).process())
            return
        raise ValueError('In dispatcher the transaction status '
                         'should be always new')

    async def add(self, transaction: Transaction) -> None:
        await self.get_best_exchanger(transaction)
