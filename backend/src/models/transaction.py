from datetime import datetime
from enum import Enum as PythonEnum

from sqlalchemy import (Column, DateTime, DECIMAL, Enum, ForeignKey,
                        Integer, String)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.future import select
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import relationship

from src.utils.random import generate_unique_name
from src.core.db import Base


class RateTypes(PythonEnum):
    FLOAT = 'float'
    FIXED = 'fixed'


class DirectionTypes(PythonEnum):
    FROM = 'from'
    TO = 'to'


class TransactionStatuses(PythonEnum):
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


class Transaction(Base):
    __tablename__ = 'transaction'
    # Transaction meta-data
    name = Column(String(6), unique=True, nullable=False)
    status_code = Column(Integer(), nullable=True)
    status = Column(
        Enum(*[status.value for status in TransactionStatuses],
             name='transaction_statuses'),
        nullable=False, default=TransactionStatuses.NEW.value)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'),
                     nullable=False)
    exchanger = Column(String(255), nullable=True)

    # Data to create order
    rate_type = Column(
        Enum(*[rate.value for rate in RateTypes], name='transaction_types'),
        nullable=False)
    from_currency = Column(String(10), nullable=False)
    from_currency_network = Column(String(10), nullable=False)
    to_currency = Column(String(10), nullable=False)
    to_currency_network = Column(String(10), nullable=False)
    direction = Column(
        Enum(*[d.value for d in DirectionTypes], name='direction_types'),
        nullable=False)
    amount = Column(DECIMAL(precision=50, scale=10), nullable=False)
    to_address = Column(String(255), nullable=False)
    tag_name = Column(String(512), nullable=True)
    tag_value = Column(String(512), nullable=True)
    refund_address = Column(String(255), nullable=True)
    refund_tag_name = Column(String(512), nullable=True)
    refund_tag_value = Column(String(512), nullable=True)

    # Transaction data (from endpoint)
    transaction_id = Column(String(255), nullable=True)
    transaction_token = Column(String(255), nullable=True)
    final_rate_type = Column(
        Enum(*[rate.value for rate in RateTypes], name='transaction_types'),
        nullable=True)
    time_registred = Column(DateTime, nullable=True)
    time_expiration = Column(DateTime, nullable=True)

    # 1.1 Final from
    final_from_currency = Column(String(10), nullable=True)
    final_from_network = Column(String(10), nullable=True)
    final_from_amount = Column(DECIMAL(precision=50, scale=10), nullable=True)
    final_from_address = Column(String(255), nullable=True)
    final_from_tag_name = Column(String(512), nullable=True)
    final_from_tag_value = Column(String(512), nullable=True)
    # 1.1.1 Final from received
    received_from_id = Column(String(512), nullable=True)
    received_from_amount = Column(DECIMAL(precision=50, scale=10),
                                  nullable=True)
    received_from_confirmations = Column(Integer(), nullable=True)

    # 1.2 Final to
    final_to_currency = Column(String(10), nullable=True)
    final_to_network = Column(String(10), nullable=True)
    final_to_amount = Column(DECIMAL(precision=50, scale=10), nullable=True)
    final_to_address = Column(String(255), nullable=True)
    final_to_tag_name = Column(String(512), nullable=True)
    final_to_tag_value = Column(String(512), nullable=True)
    # 1.2.1 Final to received
    received_to_id = Column(String(512), nullable=True)
    received_to_amount = Column(DECIMAL(precision=50, scale=10),
                                nullable=True)
    received_to_confirmations = Column(Integer(), nullable=True)

    # 1.3 Final back (returned)
    final_back_currency = Column(String(10), nullable=True)
    final_back_network = Column(String(10), nullable=True)
    final_back_amount = Column(DECIMAL(precision=50, scale=10), nullable=True)
    final_back_address = Column(String(255), nullable=True)
    final_back_tag_name = Column(String(512), nullable=True)
    final_back_tag_value = Column(String(512), nullable=True)
    # 1.3.1 Final back received
    received_back_id = Column(String(512), nullable=True)
    received_back_amount = Column(DECIMAL(precision=50, scale=10),
                                  nullable=True)
    received_back_confirmations = Column(Integer(), nullable=True)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, nullable=False)

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
