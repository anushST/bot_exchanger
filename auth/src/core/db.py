from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import text

from src.core.config import settings


Base = declarative_base()

engine = create_async_engine(settings.DATABASE_URL)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession)


async def get_async_session():
    async with AsyncSessionLocal() as async_session:
        yield async_session


@asynccontextmanager
async def get_async_session_generator():
    async with AsyncSessionLocal() as async_session:
        yield async_session


async def set_isolation_level(isolation_level: str = 'SERIALIZABLE'):
    valid_isolation_levels = (
        'READ COMMITTED', 'REPEATABLE READ',
        'SERIALIZABLE', 'READ UNCOMMITTED',)

    if isolation_level not in valid_isolation_levels:
        raise ValueError(f"Invalid isolation level: {isolation_level}")

    async with engine.connect() as connection:
        await connection.execute(text(
            'SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION '
            f'LEVEL {isolation_level}'))
        await connection.commit()
