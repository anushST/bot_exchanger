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
    to_coin: str
    in_amount: Decimal
    out_amount: Decimal
    to_network_fee: Optional[Decimal] = None
    min_from_amount: Optional[Decimal] = None
    min_to_amount: Optional[Decimal] = None
    max_from_amount: Optional[Decimal] = None
    max_to_amount: Optional[Decimal] = None
