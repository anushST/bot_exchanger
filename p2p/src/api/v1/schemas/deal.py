from pydantic import BaseModel, validator
from pydantic.types import Decimal
from typing import Optional
import uuid
from datetime import datetime

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str

    class Config:
        orm_mode = True

class CurrencyResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str

    class Config:
        orm_mode = True

class BankResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str

    class Config:
        orm_mode = True

class NetworkResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str

    class Config:
        orm_mode = True

class ArbitragerResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CreateDealRequest(BaseModel):
    buyer_identifier: uuid.UUID
    deal_type: str
    price: Decimal
    fiat_currency_code: str
    crypto_currency_code: str
    fiat_amount: Decimal
    bank_code: Optional[str] = None
    network_code: Optional[str] = None
    crypto_address: Optional[str] = None
    arbitrator_id: Optional[str] = None

    @validator('deal_type')
    def validate_deal_type(cls, v):
        if v not in ["buy", "sell"]:
            raise ValueError('deal_type должен быть "buy" или "sell"')
        return v

    @validator('price', 'fiat_amount')
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('price и fiat_amount должны быть положительными')
        return v

class DealResponse(BaseModel):
    id: uuid.UUID
    buyer: UserResponse
    arbitrator: Optional[ArbitragerResponse]
    arbitrator_offer_id: Optional[uuid.UUID]
    fiat_currency: CurrencyResponse
    crypto_currency: CurrencyResponse
    fiat_amount: Decimal
    crypto_amount: Decimal
    bank: Optional[BankResponse]
    network: Optional[NetworkResponse]
    crypto_address: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True