import asyncio
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .transaction_notifyer import TransactionNotifier
from src.database import get_session
from src.models import Transaction

logger = logging.getLogger(__name__)


class TransactionNotifyProcessor:

    def __init__(self, notifier: TransactionNotifier) -> None:
        self.notifier = notifier

    async def process_transactions(self) -> None:
        while True:
            try:
                async with get_session() as session:
                    result = await session.execute(
                        select(Transaction).where(
                            Transaction.is_status_handled.is_(False)
                        )
                    )
                    transactions = result.scalars().all()

                    for transaction in transactions:
                        await self._process_transaction(transaction, session)

            except SQLAlchemyError as e:
                logger.error(f'Ошибка при работе с базой данных: {e}')
            except Exception as e:
                logger.error(f'Неизвестная ошибка: {e}', exc_info=True)
            await asyncio.sleep(3)

    async def _process_transaction(self, transaction: Transaction,
                                   session: AsyncSession) -> None:
        try:
            transaction.is_status_handled = True
            await session.commit()

            await self.notifier.notify(transaction)
            logger.info('Уведомление успешно отправлено для транзакции '
                        f'{transaction.id}')

        except SQLAlchemyError as e:
            logger.error(
                f'Ошибка при обновлении транзакции {transaction.id}: {e}',
                exc_info=True)
            await session.rollback()
        except Exception as e:
            logger.error(
                f'Ошибка при обработке транзакции {transaction.id}: {e}',
                exc_info=True)
