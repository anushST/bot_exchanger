from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from .order import Direction, OrderType


class CreatePrice(BaseModel):
    type: OrderType
    from_ccy: str = Field(..., alias='fromCcy')
    to_ccy: str = Field(..., alias='toCcy')
    direction: Direction
    amount: Decimal
    usd: Optional[bool] = True
    refcode: Optional[str] = None
    afftax: Optional[float] = None


class AssetData(BaseModel):
    code: str
    network: str
    coin: str
    amount: Optional[str]
    rate: Optional[str]
    precision: Optional[int]
    min: Optional[str]
    max: Optional[str]
    usd: Optional[str]
    btc: Optional[str]


class CciesData(BaseModel):
    code: str
    recv: bool
    send: bool


class PriceData(BaseModel):
    from_: AssetData
    to: AssetData
    errors: list[str]
    ccies: Optional[list[CciesData]]


class RatesSchema(BaseModel):
    from_coin: str
    to_coin: str = Field(..., alias='to')
    in_amount: Decimal
    out_amount: Decimal = Field(..., alias='out')
    amount: Decimal
    tofee: Optional[Decimal] = None
    tofee_currency: Optional[str] = None
    min_amount: Decimal = Field(..., alias='minamount')
    max_amount: Decimal = Field(..., alias='maxamount')
