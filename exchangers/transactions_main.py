import asyncio
import logging

from sqlalchemy.future import select

from src.database import session_factory
from src.models import Transaction, TransactionStatuses

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    async with session_factory() as session:
        while True:
            try:
                result = await session.execute(
                    select(Transaction).where(
                        Transaction.status == TransactionStatuses.NEW)
                )
                transactions = result.scalars().all()

                if transactions:
                    pass
                else:
                    logger.info('No new transactions')

                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f'Error: {e}')
                await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())
