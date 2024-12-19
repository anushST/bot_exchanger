import asyncio
import logging

from sqlalchemy.future import select

from src.database import get_session, set_isolation_level
from src.models import Transaction, TransactionStatuses
from src.transaction.dispatcher import TransactionDispatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    dispatcher = TransactionDispatcher()
    await set_isolation_level('SERIALIZABLE')
    while True:
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(Transaction).where(
                        Transaction.status == TransactionStatuses.NEW
                        and Transaction.is_dispatcher_handled.is_(False))
                )
                transactions = result.scalars().all()

                if transactions:
                    for transaction in transactions:
                        transaction.status = TransactionStatuses.HANDLED
                        await session.commit()
                        await session.refresh(transaction)
                        await dispatcher.add(transaction)

            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f'Error: {e}', exc_info=True)
            await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())
