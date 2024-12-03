import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.database import connect, Base
from src.handlers import init_handlers
from src.middlewares import init_middlewares
from src.config import DB_LINK, TOKEN, ADMINS, TIMEZONE
from src.models import init_models

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

db, session = connect(DB_LINK, logger)
init_models(db)

scheduler = AsyncIOScheduler(timezone=TIMEZONE)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

dispatcher = Dispatcher(storage=MemoryStorage())
init_middlewares(dispatcher, session)

async def run():
    init_handlers(dispatcher)
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run())
