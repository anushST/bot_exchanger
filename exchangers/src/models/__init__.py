# flake8: noqa: F401
from sqlalchemy.ext.asyncio import AsyncEngine

from .transaction import (DirectionTypes,  EmergencyChoices, EmergencyStatuses,
                          RateTypes, Transaction, TransactionStatuses)
from .user import User
from src.database import Base


async def init_models(db: AsyncEngine):
    async with db.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
