from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CreateTransaction(BaseModel):
    user_id: int = None
    rate_type: str = None
    currency_from: str = None
    currency_from_network: str = None
    currency_to: str = None
    currency_to_network: str = None
    exchange_direction: str = None
    amount_value: Decimal = Field(None, gt=0)
    wallet_address: str = None
    tag_value: Optional[str] = None
    tag_name: Optional[str] = None


class Transaction(BaseModel):
    name: str
    status: str
