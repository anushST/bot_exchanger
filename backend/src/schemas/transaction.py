from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.models import TransactionStatuses


class TransactionStatusesEnum(Enum, TransactionStatuses):
    pass


class CreateTransaction(BaseModel):
    user_id: int
    rate_type: str
    currency_from: str
    currency_from_network: str
    currency_to: str
    currency_to_network: str
    exchange_direction: str
    amount_value: Decimal = Field(..., gt=0)
    wallet_address: str
    tag_value: Optional[str] = None
    tag_name: Optional[str] = None


class Transaction(BaseModel):
    name: str
    status: TransactionStatuses
