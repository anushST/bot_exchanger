import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, DECIMAL, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.db import Base
from src.enums import DealStatus


class Deal(Base):
    __tablename__ = 'p2p_deals'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey('users.id'),
                      nullable=False)
    arbitrager_offer_id = Column(UUID(as_uuid=True),
                                 ForeignKey('p2p_arbitrager_offers.id'),
                                 nullable=True)
    fiat_amount = Column(DECIMAL(10, 2), nullable=False)
    crypto_amount = Column(DECIMAL(10, 4), nullable=False)

    bank_id = Column(UUID, ForeignKey('p2p_banks.id'), nullable=True)
    network_id = Column(UUID, ForeignKey('p2p_networks.id'), nullable=True)

    is_buyer_confirmed = Column(Boolean, default=False, nullable=False)
    is_arbitrager_confirmed = Column(Boolean, default=False, nullable=False)

    status = Column(Enum(*[d.value for d in DealStatus],
                         name='p2p_deal_status'), nullable=False,
                    default=DealStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    messages = relationship('ChatMessage', back_populates='deal',
                            cascade='all, delete-orphan')
    appeal = relationship('Appeal', back_populates='deal', lazy='joined')
    buyer = relationship("User", lazy="joined")
    bank = relationship("Bank", lazy="joined")
    network = relationship("Network", lazy="joined")
    offer = relationship(
        "Offer",
        back_populates="deals",
        lazy="joined"
    )
