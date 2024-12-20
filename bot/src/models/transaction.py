from sqlalchemy import (Boolean, Column, DECIMAL, Enum, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.future import select
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import relationship

from src.database import BaseModel
from src.utils.random import generate_unique_name


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
    CREATED = 'created'  # Transaction has been created
    PENDING = 'pending'  # Transaction received, pending confirmation
    EXCHANGE = 'exchange'  # Transaction confirmed, exchange in progress
    WITHDRAW = 'withdraw'  # Sending funds
    DONE = 'done'  # Order completed
    EXPIRED = 'expired'  # Order expired
    EMERGENCY = 'emergency'  # Emergency, customer choice required
    ERROR = 'error'  # when some error oqqurs
    OPTIONS = (NEW, HANDLED, CREATED, PENDING, EXCHANGE, WITHDRAW, DONE,
               EXPIRED, EMERGENCY, ERROR,)


class Transaction(BaseModel):
    __tablename__ = 'transaction'
    name = Column(String(6), unique=True, nullable=False)
    status_code = Column(Integer(), nullable=True)
    msg = Column(Text(), nullable=True)
    rate_type = Column(Enum(*RateTypes.CHOICES, name='transaction_types'),
                       nullable=False)
    from_currency = Column(String(10), nullable=False)
    from_currency_network = Column(String(10), nullable=False)
    to_currency = Column(String(10), nullable=False)
    to_currency_network = Column(String(10), nullable=False)
    direction = Column(Enum(*DirectionTypes.CHOICES, name='direction_types'),
                       nullable=False)
    amount = Column(DECIMAL(precision=50, scale=10), nullable=False)
    to_address = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'),
                     nullable=False)
    status = Column(Enum(*TransactionStatuses.OPTIONS,
                         name='transaction_statuses'),
                    nullable=False, default=TransactionStatuses.NEW)
    transaction_id = Column(String(255), nullable=True)
    transaction_token = Column(String(255), nullable=True)
    is_status_showed = Column(Boolean, nullable=False, default=True)
    extra_data = Column(JSON, nullable=True)
    final_from_amount = Column(DECIMAL(precision=50, scale=10), nullable=True)
    final_to_amount = Column(DECIMAL(precision=50, scale=10), nullable=True)
    address_to_send_amount = Column(String(255), nullable=True)

    user = relationship('User', lazy='joined')

    def to_dict(self):
        return ({column.key: getattr(self, column.key)
                 for column in inspect(self).mapper.column_attrs})

    @staticmethod
    async def create_unique_name(session):
        while True:
            name = generate_unique_name(length=6)
            existing = await session.execute(
                select(Transaction).where(Transaction.name == name)
            )
            if not existing.scalar():
                return name
