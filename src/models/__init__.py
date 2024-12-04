import importlib

from sqlalchemy.ext.asyncio import AsyncEngine

from src.database import BaseModel

MODELS = ['user', 'transaction', 'currency']


async def init_models(db: AsyncEngine):
    for router in MODELS:
        importlib.import_module("." + router, package=__name__)

    async with db.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
