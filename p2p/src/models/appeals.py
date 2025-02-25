import uuid
from datetime import datetime
from enum import Enum as pyEnum

from sqlalchemy import Column, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.db import Base


class ModerationStatusEnum(str, pyEnum):
    OPEN = "OPEN"  # Запрос отправлен, ожидает обработки
    IN_PROGRESS = "IN_PROGRESS"  # Модератор начал разбирательство
    RESOLVED = "RESOLVED"  # Вопрос решён
    REJECTED = "REJECTED"  # Запрос отклонён


class ModerationRequest(Base):
    __tablename__ = 'p2p_moderation_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    deal_id = Column(UUID, ForeignKey('deals.id'), nullable=False)
    requested_by = Column(UUID, ForeignKey('users.id'), nullable=False)
    status = Column(Enum(*[s.value for s in ModerationStatusEnum]),
                    nullable=False,
                    default=ModerationStatusEnum.OPEN)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    deal = relationship("Deal", back_populates="moderation_requests",
                        lazy='select')
    requester = relationship("User", back_populates="moderation_requests",
                             lazy='select')
