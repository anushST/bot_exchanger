import asyncio
import logging
import logging.handlers
import os

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from src.database import get_session, set_isolation_level
from src.models import Transaction, TransactionStatuses
from src.transaction.dispatcher import TransactionDispatcher

if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s|%(name)s|%(levelname)s|%(message)s|',
    handlers=[
        logging.handlers.RotatingFileHandler(
            'logs/transactions.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    logger.info('Transaction processing started.')
    try:
        dispatcher = TransactionDispatcher()
        await set_isolation_level('SERIALIZABLE')
    except Exception as e:
        logger.critical(f'Failed to set database isolation level: {e}',
                        exc_info=True)
        return

    while True:
        try:
            async with get_session() as session:
                try:
                    result = await session.execute(
                        select(Transaction).where(
                            Transaction.status == TransactionStatuses.NEW)
                    )
                    transactions = result.scalars().all()

                    if transactions:
                        for transaction in transactions:
                            try:
                                transaction.status = TransactionStatuses.HANDLED # noqa
                                await session.commit()
                                await session.refresh(transaction)

                                await dispatcher.add(transaction)
                            except Exception as transaction_error:
                                logger.error(
                                    f'Failed to process transaction {transaction.id}: {transaction_error}', # noqa
                                    exc_info=True
                                )
                                await session.rollback()

                except SQLAlchemyError as db_error:
                    logger.error('Database error during transaction '
                                 f'query: {db_error}', exc_info=True)
                    await asyncio.sleep(5)
        except Exception as e:
            logger.error(f'Unexpected error in main loop: {e}', exc_info=True)
            await asyncio.sleep(5)

        await asyncio.sleep(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Transaction processing stopped manually.')
    except Exception as e:
        logger.critical(f'Critical error in application: {e}', exc_info=True)
