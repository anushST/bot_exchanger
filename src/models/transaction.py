from sqlalchemy import Column, DECIMAL, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import BaseModel


class TransactionTypes:
    FLOAT = 'float'
    FIXED = 'fixed'
    CHOICES = (FLOAT, FIXED)


class DirectionTypes:
    FROM = 'from'
    TO = 'to'
    CHOICES = (FROM, TO)


class Transaction(BaseModel):
    __tablename__ = 'transaction'
    type = Column(Enum(*TransactionTypes.CHOICES, name='transaction_types'),
                  nullable=False)
    from_ccy = Column(String(10), nullable=False)
    to_ccy = Column(String(10), nullable=False)
    direction = Column(Enum(*DirectionTypes.CHOICES, name='direction_types'),
                       nullable=False)
    amount = Column(DECIMAL(precision=50, scale=30), nullable=False)
    to_address = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'),
                     nullable=False)
    user = relationship('User', back_populates='transactions')
