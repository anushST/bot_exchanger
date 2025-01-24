from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CreateTransaction(BaseModel):
    rate_type: str
    currency_from: str
    currency_from_network: str
    currency_to: str
    currency_to_network: str
    exchange_direction: str
    amount_value: Decimal = Field(..., gt=0)
    wallet_address: str
    return_address: Optional[str] = None
    tag_value: Optional[str] = None


class Transaction(BaseModel):
    name: str
    status: str
