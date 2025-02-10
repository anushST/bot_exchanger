from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class RatesSchema(BaseModel):
    from_coin: str
    to_coin: str
    in_amount: Decimal
    out_amount: Decimal
    to_network_fee: Optional[Decimal] = None
    min_from_amount: Optional[Decimal] = None
    min_to_amount: Optional[Decimal] = None
    max_from_amount: Optional[Decimal] = None
    max_to_amount: Optional[Decimal] = None
