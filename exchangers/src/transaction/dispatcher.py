import asyncio
import logging

from src.models import Transaction, TransactionStatuses
from .ffio_transaction import FFioTransaction
from .changelly_transaction import ChangellyTransaction
from .schemas import CreateBestPrice

from src.api.changelly import changelly_client
from src.api.ffio.ffio_client import ffio_client

logger = logging.getLogger(__name__)


async def get_best_price(transaction: Transaction):
    best_price = CreateBestPrice(
        type=transaction.rate_type,
        from_currency=transaction.from_currency,
        to_currency=transaction.to_currency,
        from_network=transaction.from_currency_network,
        to_network=transaction.to_currency_network,
        direction=transaction.direction,
        amount=transaction.amount
    )
    ffio = await ffio_client.get_rate(best_price)
    changelly = await changelly_client.get_rate(best_price)
    if ffio:
        logger.info(f'FFIO: {ffio.to_amount}, Changelly {changelly.to_amount}')
    else:
        logger.info(f'Changelly {changelly.from_amount}')
    if ffio and ffio.to_amount < changelly.to_amount:
        logger.info('Handled by ffio')
        asyncio.create_task(FFioTransaction(transaction.id).process())
    else:
        logger.info('Handled by changelly')
        asyncio.create_task(ChangellyTransaction(transaction.id).process())


class TransactionDispatcher:
    """Dispatch transaction to a exchanger."""

    async def get_best_exchanger(self, transaction: Transaction) -> None:
        if transaction.status == TransactionStatuses.HANDLED.value:
            asyncio.create_task(FFioTransaction(transaction.id).process())
            # await get_best_price(transaction)
            return
        raise ValueError('In dispatcher the transaction status '
                         'should be always new')

    async def add(self, transaction: Transaction) -> None:
        await self.get_best_exchanger(transaction)
