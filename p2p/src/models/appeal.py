import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.enums import ModerationStatus
from src.core.db import Base


class ModerationRequest(Base):
    __tablename__ = 'p2p_moderation_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    deal_id = Column(UUID(as_uuid=True), ForeignKey('p2p_deals.id'),
                     nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey('user.id'),
                          nullable=False)
    status = Column(Enum(*[s.value for s in ModerationStatus],
                         name='p2p_moderation_status'),
                    nullable=False,
                    default=ModerationStatus.OPEN.value,)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    deal = relationship("Deal", back_populates="moderation_requests",
                        lazy='joined')
    requester = relationship("User", back_populates="moderation_requests",
                             lazy='joined')
