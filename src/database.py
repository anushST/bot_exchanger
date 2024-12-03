from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()

async def connect(connect_string, logger):
    try:
        engine = create_async_engine(connect_string)
        engine.connect()
        session = sessionmaker(autocommit=False, autoflush=False, bind=engine,
                               class_=AsyncSession)
        return engine, session
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
