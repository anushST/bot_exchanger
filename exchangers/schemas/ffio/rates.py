from decimal import Decimal

from pydantic import BaseModel


class RatesSchema(BaseModel):
    from_coin: str
    to_coin: str
    in_amount: Decimal
    out_amount: Decimal
    amount: Decimal
    tofee: Decimal
    tofee_currency: str
    minamount: Decimal
    maxamount: Decimal
