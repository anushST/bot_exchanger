# flake8: noqa: F401
from sqlalchemy.ext.asyncio import AsyncEngine

from .transaction import DirectionTypes, RateTypes, Transaction, TransactionStatuses
from .user import User
from src.database import BaseModel


async def init_models(db: AsyncEngine):
    async with db.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
