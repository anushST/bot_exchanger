from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class RatesSchemaResponse(BaseModel):
    from_coin: str
    to_coin: str = Field(..., alias='to')
    in_amount: Decimal
    out_amount: Decimal = Field(..., alias='out')
    amount: Decimal
    tofee: Optional[Decimal] = None
    tofee_currency: Optional[str] = None
    min_amount: Decimal = Field(..., alias='minamount')
    max_amount: Decimal = Field(..., alias='maxamount')
