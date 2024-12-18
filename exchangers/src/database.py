from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import config

Base = declarative_base()
engine = create_async_engine(config.DATABASE_URL)
engine.connect()
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine,
                               class_=AsyncSession)


async def get_session():
    async with session_factory() as session:
        yield session
