import uuid
from datetime import datetime

from sqlalchemy import (
    Column, BigInteger, Boolean, Enum, DateTime, String)
from sqlalchemy.dialects.postgresql import UUID

from src.core.db import Base
from src.enums import UserRole


class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    tg_id = Column(BigInteger, unique=True, nullable=True)
    role = Column(Enum(*[r.value for r in UserRole],
                       name='user_role'),
                  nullable=False,
                  default=UserRole.USER.value)
    language = Column(String(2), nullable=False, default="ru")
    is_active = Column(Boolean(), nullable=False, default=True)
    is_email_confirmed = Column(Boolean(), nullable=False, default=False)
    last_active_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)
