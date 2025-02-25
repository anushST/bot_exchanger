import uuid
from datetime import datetime

from sqlalchemy import Column, Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .currencies import arbitrator_banks
from src.core.db import Base


class Banks(Base):
    __tablename__ = 'banks'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    country = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)
    arbitrators = relationship("Arbitrager", secondary=arbitrator_banks,
                               back_populates="p2p_banks")
