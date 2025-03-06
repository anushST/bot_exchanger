import asyncio
import logging
import logging.config
import logging.handlers
import os

from src.core.db import engine as db, set_isolation_level
from src.core.config import LOGGING_CONFIG
from src.models import init_models
from src.notifications.process import consume


if not os.path.exists('logs'):
    os.makedirs('logs')

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


async def init_db():
    try:
        await init_models(db)
        await set_isolation_level('SERIALIZABLE')
    except Exception as e:
        logger.critical('Error while initializing database: %s', e,
                        exc_info=True)
        raise


async def main():
    await init_db()
    await consume()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Server stopped manually.')
    except Exception as e:
        logger.critical(f'Critical error in application: {e}', exc_info=True)
