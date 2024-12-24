from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .emergency import EmergencyChoice


class OrderType(Enum):
    fixed = "fixed"
    float = "float"


class Direction(Enum):
    from_ = "from"
    to = "to"


class OrderStatus(Enum):
    NEW = "NEW"
    PENDING = "PENDING"
    EXCHANGE = "EXCHANGE"
    WITHDRAW = "WITHDRAW"
    DONE = "DONE"
    EXPIRED = "EXPIRED"
    EMERGENCY = "EMERGENCY"


class EmergencyStatus(Enum):
    EXPIRED = "EXPIRED"
    LESS = "LESS"
    MORE = "MORE"
    LIMIT = "LIMIT"


class _TransactionDetails(BaseModel):
    id: Optional[str] = None
    amount: Optional[Decimal] = None
    fee: Optional[str] = None
    ccyfee: Optional[str] = None
    time_reg: Optional[int] = Field(None, alias='timeReg')
    time_block: Optional[int] = Field(None, alias='timeBlock')
    confirmations: Optional[int] = None


class _CurrencyInfo(BaseModel):
    code: Optional[str] = None
    coin: Optional[str] = None
    network: Optional[str] = None
    name: Optional[str] = None
    alias: Optional[str] = None
    amount: Optional[Decimal] = None
    address: Optional[str] = None
    tag_value: Optional[str] = Field(None, alias='tag')
    tag_name: Optional[str] = Field(None, alias='tagName')
    address_mix: Optional[str] = Field(None, alias='addressMix')
    req_confirmations: Optional[int] = Field(None, alias='reqConfirmations')
    max_confirmations: Optional[int] = Field(None, alias='maxConfirmations')
    tx: _TransactionDetails


class _EmergencyInfo(BaseModel):
    status: Optional[list[EmergencyStatus]] = []
    choice: Optional[EmergencyChoice] = None
    repeat: Optional[bool] = None


class _OrderTime(BaseModel):
    reg: Optional[int] = None
    start: Optional[int] = None
    finish: Optional[int] = None
    update: Optional[int] = None
    expiration: Optional[int] = None
    left: Optional[int] = None


class CreateOrder(BaseModel):
    type: OrderType
    from_ccy: str = Field(..., alias='fromCcy')
    to_ccy: str = Field(..., alias='toCcy')
    direction: Direction
    amount: Decimal
    to_address: str = Field(..., alias='toAddress')
    tag: Optional[str] = None
    refcode: Optional[str] = None
    afftax: Optional[float] = None


class CreateOrderDetails(BaseModel):
    id: str
    token: str


class OrderData(BaseModel):
    token: str
    id: str
    type: OrderType
    email: str
    status: OrderStatus
    time: _OrderTime
    from_info: _CurrencyInfo = Field(..., alias='from')
    to_info: _CurrencyInfo = Field(..., alias='to')
    back_info: _CurrencyInfo = Field(..., alias='back')
    emergency: Optional[_EmergencyInfo] = None
