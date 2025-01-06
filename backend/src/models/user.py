from datetime import datetime

from sqlalchemy import Column, BigInteger, DateTime, String

from src.core.db import Base


class User(Base):
    __tablename__ = 'user'
    tg_id = Column(BigInteger, unique=True, nullable=False)
    tg_name = Column(String(255), nullable=False)
    tg_username = Column(String(255), nullable=True)
    language = Column(String(2), nullable=False, default="ru")
    created_on = Column(DateTime, default=datetime.now, nullable=False)
    updated_on = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)
