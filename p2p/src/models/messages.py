import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Enum, String)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.core.db import Base
from src.enums import MessageType


class ChatMessage(Base):
    __tablename__ = 'p2p_chat_messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    deal_id = Column(UUID(as_uuid=True), ForeignKey('p2p_deals.id'),
                     nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey('users.id'),
                       nullable=False)
    message_type = Column(Enum(*[s.value for s in MessageType],
                               name='p2p_message_type'),
                          nullable=False,
                          default=MessageType.TEXT.value)
    attachment_url = Column(String, nullable=True)
    message_content = Column(String, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    is_from_moderator = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

    deal = relationship('Deal', back_populates='messages', lazy='joined')
