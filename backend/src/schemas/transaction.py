from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.models import DirectionTypes, RateTypes, TransactionStatuses


class BaseRate(BaseModel):
    rate_type: RateTypes
    currency_from: str
    currency_from_network: str
    currency_to: str
    currency_to_network: str


class CreateTransaction(BaseRate):
    exchange_direction: DirectionTypes
    amount_value: Decimal = Field(..., gt=0)
    wallet_address: str
    refund_address: Optional[str] = None
    tag_value: Optional[str] = None
    refund_tag_value: Optional[str] = None


class TransactionSummary(BaseModel):
    transaction_id: str
    status: TransactionStatuses
    from_amount: Decimal = Field(..., gt=0)
    from_currency: str
    to_amount: Decimal = Field(..., gt=0)
    to_currency: str
    time_created: datetime


class Transaction(BaseRate):
    transaction_id: str
    status: str
    status_code: int

    from_amount: Decimal = Field(..., gt=0)
    to_amount: Decimal = Field(..., gt=0)
    from_address: str
    to_address: str
    refund_address: Optional[str] = None
    from_tag_name: Optional[str] = None
    to_tag_name: Optional[str] = None
    refund_tag_name: Optional[str] = None
    from_tag_value: Optional[str] = None
    to_tag_value: Optional[str] = None
    refund_tag_value: Optional[str] = None
    time_expiration: datetime

    received_from_id: Optional[str] = None
    received_from_amount: Optional[Decimal] = Field(None, gt=0)
    received_from_confirmations: Optional[int] = None

    received_to_id: Optional[str] = None
    received_to_amount: Optional[Decimal] = Field(None, gt=0)
    received_to_confirmations: Optional[int] = None

    received_back_id: Optional[str] = None
    received_back_amount: Optional[Decimal] = Field(None, gt=0)
    received_back_confirmations: Optional[int] = None
