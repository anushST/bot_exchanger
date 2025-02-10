from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from .user import User
from src.models import RateTypes, TransactionStatuses


class BaseRate(BaseModel):
    rate_type: RateTypes
    currency_from: str
    currency_from_network: str
    currency_to: str
    currency_to_network: str


class TransactionSummary(BaseModel):
    rate_type: Optional[RateTypes] = None
    transaction_id: Optional[str] = None
    status: Optional[TransactionStatuses] = None
    from_amount: Optional[Decimal] = Field(None, gt=0)
    from_currency: Optional[str] = None
    to_amount: Optional[Decimal] = Field(None, gt=0)
    to_currency: Optional[str] = None
    time_created: Optional[datetime] = None


class Transaction(BaseRate):
    user: Optional[User]
    transaction_id: Optional[str]
    status: Optional[str]
    status_code: Optional[int]

    from_amount: Optional[Decimal] = Field(None, gt=0)
    to_amount: Optional[Decimal] = Field(None, gt=0)
    from_address: Optional[str]
    to_address: Optional[str]
    refund_address: Optional[str] = None
    from_tag_name: Optional[str] = None
    to_tag_name: Optional[str] = None
    refund_tag_name: Optional[str] = None
    from_tag_value: Optional[str] = None
    to_tag_value: Optional[str] = None
    refund_tag_value: Optional[str] = None
    time_expiration: Optional[datetime] = None
    created_at: Optional[datetime] = None

    received_from_id: Optional[str] = None
    received_from_amount: Optional[Decimal] = Field(None, gt=0)
    received_from_confirmations: Optional[int] = None

    received_to_id: Optional[str] = None
    received_to_amount: Optional[Decimal] = Field(None, gt=0)
    received_to_confirmations: Optional[int] = None

    received_back_id: Optional[str] = None
    received_back_amount: Optional[Decimal] = Field(None, gt=0)
    received_back_confirmations: Optional[int] = None
