from datetime import datetime

from sqlalchemy import Column, BigInteger, DateTime, String, Boolean

from src.core.db import Base


class AdminUser(Base):
    __tablename__ = 'admin_user'
    tg_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_active_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)
