import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.database import engine as db, session
from src.handlers import init_handlers
from src.middlewares import init_middlewares
from src.config import TOKEN, TIMEZONE
from src.models import init_models

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def init_db():
    await init_models(db)
    return db, session


async def init_bot():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    dispatcher = Dispatcher(storage=MemoryStorage())
    return bot, dispatcher


async def init_scheduler():
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.start()
    return scheduler


async def run():
    db, session = await init_db()
    bot, dispatcher = await init_bot()

    init_middlewares(dispatcher, session)
    init_handlers(dispatcher)

    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run())
