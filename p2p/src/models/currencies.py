import uuid
from datetime import datetime
from enum import Enum as pyEnum

from sqlalchemy import (
    Column, Boolean, DateTime, String, Enum, Table, ForeignKey)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.core.db import Base


class CurrencyTypeEnum(str, pyEnum):
    FIAT = "FIAT"
    CRYPTO = "CRYPTO"


currency_networks = Table(
    'currency_networks',
    Base.metadata,
    Column('currency_id', UUID, ForeignKey('currencies.id'), primary_key=True),
    Column('network_id', UUID, ForeignKey('networks.id'), primary_key=True)
)


class Currency(Base):
    __tablename__ = 'p2p_currencies'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    type = Column(Enum(*[t.value for t in CurrencyTypeEnum]), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    networks = relationship("Network", secondary=currency_networks,
                            back_populates="p2p_currencies", lazy='joined')


class Network(Base):
    __tablename__ = 'p2p_networks'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    currencies = relationship("Currency", secondary=currency_networks,
                              back_populates="p2p_networks", lazy='joined')
