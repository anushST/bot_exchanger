from src.models import Transaction, TransactionStatuses


class TransactionDispatcher:
    """Dispatch transaction to a exchanger."""

    async def get_best_exchanger(self, transaction: Transaction) -> None:
        if transaction.status == TransactionStatuses.NEW:
            pass
        raise Exception('In dispatcher the transaction status '
                        'should be always new')

    async def add(self, transaction: Transaction) -> None:
        await self.get_best_exchanger(transaction)
