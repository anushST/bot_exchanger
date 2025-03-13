import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.enums import AppealStatus
from src.core.db import Base


class Appeal(Base):
    __tablename__ = 'p2p_appeals'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    deal_id = Column(UUID(as_uuid=True), ForeignKey('p2p_deals.id'),
                     nullable=False, unique=True)
    requested_by_id = Column(UUID(as_uuid=True), ForeignKey('users.id'),
                             nullable=False)
    status = Column(Enum(*[s.value for s in AppealStatus],
                         name='p2p_moderation_status'),
                    nullable=False,
                    default=AppealStatus.IN_PROGRESS.value,)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    deal = relationship('Deal', lazy='joined', back_populates='appeal')
    requested_by = relationship('User', lazy='joined')
