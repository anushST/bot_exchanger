# flake8: noqa: F401
from sqlalchemy.ext.asyncio import AsyncEngine

from .user import User, UserRole
from src.core.db import Base


async def init_models(db: AsyncEngine):
    async with db.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
