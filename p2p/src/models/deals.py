import uuid
from datetime import datetime
from enum import Enum as pyEnum

from sqlalchemy import Column, DateTime, DECIMAL, ForeignKey, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.db import Base


class DealStatusEnum(str, pyEnum):
    PENDING = "PENDING"  # Ожидание оплаты
    PAID = "PAID"  # Оплата подтверждена
    COMPLETED = "COMPLETED"  # Сделка завершена
    CANCELED = "CANCELED"  # Отмена сделки
    MODERATION = "MODERATION"  # Сделка на модерации


class Deal(Base):
    __tablename__ = 'p2p_deals'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    buyer_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    arbitrator_id = Column(UUID, ForeignKey('users.id'), nullable=True)
    arbitrator_offer_id = Column(UUID, ForeignKey('arbitrator_offers.id'),
                                 nullable=True)

    fiat_currency_id = Column(
        UUID, ForeignKey('currencies.id'), nullable=False)
    crypto_currency_id = Column(
        UUID, ForeignKey('currencies.id'), nullable=False)
    fiat_amount = Column(DECIMAL(10, 2), nullable=False)
    crypto_amount = Column(DECIMAL(10, 4), nullable=False)

    bank_id = Column(UUID, ForeignKey('banks.id'), nullable=True)
    network_id = Column(UUID, ForeignKey('networks.id'), nullable=True)
    crypto_address = Column(String, nullable=True)

    status = Column(Enum(*[d.value for d in DealStatusEnum]), nullable=False,
                    default=DealStatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    buyer = relationship("User", foreign_keys=[buyer_id],
                         back_populates="bought_deals", lazy='select')
    arbitrator = relationship("User", foreign_keys=[arbitrator_id],
                              back_populates="arbitrated_deals", lazy='select',
                              uselist=False)
    arbitrator_offer = relationship("ArbitratorOffer", back_populates="deals",
                                    lazy='select', uselist=False)

    fiat_currency = relationship(
        "Currency", foreign_keys=[fiat_currency_id], lazy='select')
    crypto_currency = relationship(
        "Currency", foreign_keys=[crypto_currency_id], lazy='select')
    bank = relationship("Bank", lazy='select')
    network = relationship("Network", lazy='select')

    moderation_requests = relationship(
        "ModerationRequest", back_populates="deal", lazy='select')
