import asyncio
import decimal
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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
    await init_models(db)
    await set_isolation_level('SERIALIZABLE')
    return db, session


async def init_bot():
    bot = Bot(token=config.TOKEN,
              default=DefaultBotProperties(parse_mode='HTML'))
    dispatcher = Dispatcher(storage=MemoryStorage())
    return bot, dispatcher


async def init_scheduler():
    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
    scheduler.start()
    return scheduler


async def run():
    db, session = await init_db()
    bot, dispatcher = await init_bot()

    init_middlewares(dispatcher, session)
    init_handlers(dispatcher)

    trn_notifyer = TransactionNotifier(bot)
    trn_notify_processor = TransactionNotifyProcessor(trn_notifyer)

    asyncio.create_task(trn_notify_processor.process_transactions())

    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run())
