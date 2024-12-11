from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from enum import Enum


class OrderType(Enum):
    fixed = "fixed"
    float = "float"


class Direction(Enum):
    from_ = "from"
    to = "to"


class CreateOrder(BaseModel):
    type: OrderType
    from_ccy: str
    to_ccy: str
    direction: Direction
    amount: Decimal
    to_address: str
    tag: Optional[bool] = None
    refcode: Optional[str] = None
    afftax: Optional[float] = None


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


class EmergencyChoice(Enum):
    NONE = "NONE"
    EXCHANGE = "EXCHANGE"
    REFUND = "REFUND"


class _TransactionDetails(BaseModel):
    id: Optional[str]
    amount: Optional[str]
    fee: Optional[str]
    ccyfee: Optional[str]
    time_reg: Optional[int]
    time_block: Optional[int]
    confirmations: Optional[int]


class _CurrencyInfo(BaseModel):
    code: Optional[str] = None
    coin: Optional[str] = None
    network: Optional[str] = None
    name: Optional[str] = None
    alias: Optional[str] = None
    amount: Optional[str] = None
    address: Optional[str] = None
    tag: Optional[str] = None
    address_mix: Optional[str] = None
    req_confirmations: Optional[int] = None
    max_confirmations: Optional[int] = None
    tx: _TransactionDetails


class _EmergencyInfo(BaseModel):
    status: Optional[list[EmergencyStatus]]
    choice: Optional[EmergencyChoice]
    repeat: Optional[bool]


class _OrderTime(BaseModel):
    reg: Optional[int]
    start: Optional[int]
    finish: Optional[int]
    update: Optional[int]
    expiration: Optional[int]
    left: Optional[int]


class OrderData(BaseModel):
    token: str
    id: str
    type: OrderType
    email: str
    status: OrderStatus
    time: _OrderTime
    from_info: _CurrencyInfo
    to_info: _CurrencyInfo
    back_info: _CurrencyInfo
    emergency: Optional[_EmergencyInfo] = None
