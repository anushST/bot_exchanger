from pydantic import BaseModel, validator
from pydantic.types import Decimal  
from typing import Optional
import uuid
from datetime import datetime

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
    buyer_id: uuid.UUID
    arbitrator_id: uuid.UUID | None
    arbitrator_offer_id: uuid.UUID | None
    fiat_currency_id: uuid.UUID
    crypto_currency_id: uuid.UUID
    fiat_amount: Decimal
    crypto_amount: Decimal
    bank_id: uuid.UUID | None
    network_id: uuid.UUID | None
    crypto_address: str | None
    status: str  
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True