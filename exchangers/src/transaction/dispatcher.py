from src.models import Transaction


class TransactionDispatcher:
    """Dispatch transaction to a exchanger."""

    async def get_best_exchanger(self) -> None:
        pass

    async def add(self, transaction: Transaction) -> None:
        pass
