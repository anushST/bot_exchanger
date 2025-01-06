import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import text

from src.config import config


class PreBase:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)

Base = declarative_base(cls=PreBase)
engine = create_async_engine(config.DATABASE_URL)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine,
                       class_=AsyncSession)


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


@asynccontextmanager
async def get_session():
    async with session() as ses:
        yield ses
