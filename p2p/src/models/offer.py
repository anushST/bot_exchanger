import uuid
from datetime import datetime

from sqlalchemy import (
    Column, Boolean, DateTime, ForeignKey, DECIMAL, Enum, Table)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.db import Base
from src.enums import OfferType


arbitrator_offer_networks = Table(
    'p2p_arbitrator_offer_networks',
    Base.metadata,
    Column('offer_id', UUID, ForeignKey('p2p_arbitrager_offers.id'),
           primary_key=True),
    Column('network_id', UUID, ForeignKey('p2p_networks.id'), primary_key=True)
)


class Offer(Base):
    __tablename__ = 'p2p_arbitrager_offers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    arbitrator_id = Column(UUID, ForeignKey('p2p_arbitragers.id'),
                           nullable=False)
    fiat_currency_id = Column(UUID, ForeignKey('p2p_currencies.id'),
                              nullable=False)
    crypto_currency_id = Column(UUID, ForeignKey('p2p_currencies.id'),
                                nullable=False)
    type = Column(Enum(*[o.value for o in OfferType],
                       name='p2p_offer_type'), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    arbitrator = relationship("Arbitrager", back_populates="offers",
                              lazy='joined')
    networks = relationship("Network", secondary=arbitrator_offer_networks,
                            back_populates="offers", lazy='joined')
