from sqlalchemy import (Boolean, Column, DateTime, DECIMAL, Enum, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.future import select
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import relationship

from src.database import Base
from src.utils.random import generate_unique_name


class RateTypes:
    FLOAT = 'float'
    FIXED = 'fixed'
    CHOICES = (FLOAT, FIXED)


class DirectionTypes:
    FROM = 'from'
    TO = 'to'
    CHOICES = (FROM, TO)


class EmergencyChoices:
    NONE = "NONE"
    EXCHANGE = "EXCHANGE"
    REFUND = "REFUND"
    CHOICES = (NONE, EXCHANGE, REFUND,)


class EmergencyStatuses:
    EXPIRED = "EXPIRED"
    LESS = "LESS"
    MORE = "MORE"
    LIMIT = "LIMIT"
    CHOICES = (EXPIRED, LESS, MORE, LIMIT,)


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


class Transaction(Base):
    __tablename__ = 'transaction'
    # Transaction meta-data
    name = Column(String(6), unique=True, nullable=False)
    status_code = Column(Integer(), nullable=True)
    status = Column(Enum(*TransactionStatuses.OPTIONS,
                         name='transaction_statuses'),
                    nullable=False, default=TransactionStatuses.NEW)
    is_status_showed = Column(Boolean, nullable=False, default=True)
    msg = Column(Text(), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'),
                     nullable=False)

    # Data to create order
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
    tag_name = Column(String(512), nullable=True)
    tag_value = Column(String(512), nullable=True)
    refund_address = Column(String(255), nullable=False)
    refund_tag_name = Column(String(512), nullable=True)
    refund_tag_value = Column(String(512), nullable=True)

    # Transaction data (from endpoint)
    transaction_id = Column(String(255), nullable=True)
    transaction_token = Column(String(255), nullable=True)
    final_rate_type = Column(Enum(*RateTypes.CHOICES,
                                  name='transaction_types'),
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

    # 1.4 Emergency
    is_emergency_handled = Column(Boolean, default=False)
    emergency_statuses = Column(String(255), nullable=True)
    emergency_choise = Column(Enum(*EmergencyChoices.CHOICES,
                                   name='emergency_choises'),
                              nullable=True)
    emergency_address = Column(String(255), nullable=True)
    emergency_tag_name = Column(String(512), nullable=True)
    emergency_tag_value = Column(String(512), nullable=True)
    made_emergency_action = Column(Boolean(), nullable=True, default=True) # Use for error address or other problems # noqa

    user = relationship('User', lazy='joined')

    def set_emergency_statuses(self, statuses: list[str]) -> bool:
        self.emergency_statuses = ':'.join(statuses)
        return True

    def get_emergency_statuses(self) -> list[str]:
        return self.emergency_statuses.split(':')

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
