import uuid
from datetime import datetime

from sqlalchemy import (
    Column, BigInteger, Enum, DateTime, String, Table, ForeignKey)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.core.db import Base
from src.enums import UserRole


class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    tg_id = Column(BigInteger, unique=True, nullable=True)
    role = Column(Enum(*[r.value for r in UserRole],
                       name='user_role'),
                  nullable=False,
                  default=UserRole.USER.value)
    language = Column(String(2), nullable=False, default="ru")
    last_active_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)


arbitrager_banks = Table(
    'p2p_arbitrager_banks',
    Base.metadata,
    Column('arbitrator_id', UUID, ForeignKey('p2p_arbitragers.id'),
           primary_key=True),
    Column('bank_id', UUID, ForeignKey('p2p_banks.id'), primary_key=True)
)


class Arbitrager(Base):
    __tablename__ = 'p2p_arbitragers'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)


class Moderator(Base):
    __tablename__ = 'p2p_moderators'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)
