import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, DECIMAL, ForeignKey, Enum, String
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
    arbitrator_id = Column(UUID(as_uuid=True),
                           ForeignKey('p2p_arbitragers.id'),
                           nullable=True)
    arbitrator_offer_id = Column(UUID(as_uuid=True),
                                 ForeignKey('p2p_arbitrager_offers.id'),
                                 nullable=True)

    fiat_currency_id = Column(
        UUID(as_uuid=True), ForeignKey('p2p_currencies.id'), nullable=False)
    crypto_currency_id = Column(
        UUID(as_uuid=True), ForeignKey('p2p_currencies.id'), nullable=False)
    fiat_amount = Column(DECIMAL(10, 2), nullable=False)
    crypto_amount = Column(DECIMAL(10, 4), nullable=False)

    bank_id = Column(UUID, ForeignKey('p2p_banks.id'), nullable=True)
    network_id = Column(UUID, ForeignKey('p2p_networks.id'), nullable=True)
    crypto_address = Column(String, nullable=True)

    status = Column(Enum(*[d.value for d in DealStatus],
                         name='p2p_deal_status'), nullable=False,
                    default=DealStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    messages = relationship('ChatMessage', back_populates='deal',
                            cascade='all, delete-orphan')

    buyer = relationship("User", lazy="joined")
    arbitrator = relationship("Arbitrager", lazy="joined")
    fiat_currency = relationship("Currency", foreign_keys=[fiat_currency_id],
                                 lazy="joined")
    crypto_currency = relationship(
        "Currency", foreign_keys=[crypto_currency_id], lazy="joined")
    bank = relationship("Bank", lazy="joined")
    network = relationship("Network", lazy="joined")
    offer = relationship(
        "Offer",
        foreign_keys=[arbitrator_offer_id],
        back_populates="deals",
        lazy="joined"
    )
