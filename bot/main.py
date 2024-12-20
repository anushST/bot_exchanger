import asyncio
import decimal
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from src.config import config
from src.database import engine as db, session, set_isolation_level
from src.handlers import init_handlers
from src.middlewares import init_middlewares
from src.models import init_models
from src.transaction import TransactionNotifier, TransactionNotifyProcessor

decimal.getcontext().prec = 8
decimal.getcontext().rounding = decimal.ROUND_DOWN

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def init_db():
    try:
        await init_models(db)
        await set_isolation_level('SERIALIZABLE')
        return db, session
    except Exception as e:
        logger.critical('Error while initializing database: %s', e,
                        exc_info=True)
        raise


async def init_bot():
    try:
        bot = Bot(token=config.TOKEN,
                  default=DefaultBotProperties(parse_mode='HTML'))
        dispatcher = Dispatcher(storage=MemoryStorage())
        return bot, dispatcher
    except Exception as e:
        logger.critical('Error while initializing bot: %s', e, exc_info=True)
        raise


async def run():
    db, session = None, None
    bot, dispatcher = None, None
    while True:
        try:
            db, session = await init_db()
            bot, dispatcher = await init_bot()

            init_middlewares(dispatcher, session)
            init_handlers(dispatcher)

            trn_notifyer = TransactionNotifier(bot)
            trn_notify_processor = TransactionNotifyProcessor(trn_notifyer)

            asyncio.create_task(trn_notify_processor.process_transactions())

            await bot.delete_webhook(drop_pending_updates=True)
            await dispatcher.start_polling(bot)
        except Exception as e:
            logger.error(f'Unexpected error in main loop: {e}', exc_info=True)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run())
