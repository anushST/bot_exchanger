from sqlalchemy import Column, DECIMAL, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from src.database import BaseModel


class RateTypes:
    FLOAT = 'float'
    FIXED = 'fixed'
    CHOICES = (FLOAT, FIXED)


class DirectionTypes:
    FROM = 'from'
    TO = 'to'
    CHOICES = (FROM, TO)


class TransactionStatuses:
    NEW = 'new'  # New order
    HANDLED = 'handled'  # Transaction handled by one of the exchangers
    PENDING = 'pending'  # Transaction received, pending confirmation
    EXCHANGE = 'exchange'  # Transaction confirmed, exchange in progress
    WITHDRAW = 'withdraw'  # Sending funds
    DONE = 'done'  # Order completed
    EXPIRED = 'expired'  # Order expired
    EMERGENCY = 'emergency'  # Emergency, customer choice required
    OPTIONS = (NEW, HANDLED, PENDING, EXCHANGE, WITHDRAW, DONE, EXPIRED,
               EMERGENCY)


class Transaction(BaseModel):
    __tablename__ = 'transaction'
    rate_type = Column(Enum(*RateTypes.CHOICES, name='transaction_types'),
                       nullable=False)
    from_currency = Column(String(10), nullable=False)
    from_currency_network = Column(String(10), nullable=False)
    to_currency = Column(String(10), nullable=False)
    to_currency_network = Column(String(10), nullable=False)
    direction = Column(Enum(*DirectionTypes.CHOICES, name='direction_types'),
                       nullable=False)
    amount = Column(DECIMAL(precision=50, scale=30), nullable=False)
    to_address = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'),
                     nullable=False)
    status = Column(Enum(*TransactionStatuses.OPTIONS,
                         name='transaction_statuses'),
                    nullable=False, default=TransactionStatuses.NEW)
    transaction_id = Column(String(255), nullable=True)
    transaction_token = Column(String(255), nullable=True)
