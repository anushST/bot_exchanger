import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import config

Base = declarative_base()
engine = create_async_engine(config.DATABASE_URL)
engine.connect()
session = sessionmaker(autocommit=False, autoflush=False, bind=engine,
                       class_=AsyncSession)

@asynccontextmanager
async def get_session():
    async with session() as ses:
        yield ses


class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    created_on = Column(DateTime, default=datetime.now, nullable=False)
    updated_on = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)
