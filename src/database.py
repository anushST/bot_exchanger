import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    created_on = Column(DateTime, default=datetime.now, nullable=False)
    updated_on = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)


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
