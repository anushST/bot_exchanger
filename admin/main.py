import asyncio
import logging
import logging.config
import logging.handlers
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import main_router
from src.core.db import engine as db, set_isolation_level
from src.core.config import settings, LOGGING_CONFIG
from src.middlewares import TelegramAuthMiddleware
from src.models import init_models
# from load_csv import load_csv_data

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

app = FastAPI(docs_url='/docs/admin/swagger',
              openapi_url='/docs/admin/openapi.json',
              title=settings.app_title)

app.include_router(main_router, prefix='/api/v1')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
# app.add_middleware(TelegramAuthMiddleware)


async def main():
    await init_db()
    # async with AsyncSessionLocal() as session:
    #     await load_csv_data(session, 'user.csv', 'transaction.csv')

    config = uvicorn.Config('main:app', host='0.0.0.0',
                            port=8001, reload=True, log_config=None)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Server stopped manually.')
    except Exception as e:
        logger.critical(f'Critical error in application: {e}', exc_info=True)
