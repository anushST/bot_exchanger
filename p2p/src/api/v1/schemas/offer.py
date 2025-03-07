from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class NetworkSchema(BaseModel):
    id: UUID
    name: str
    code: str
    is_active: bool

    class Config:
        orm_mode = True

class OfferCreateSchema(BaseModel):
    fiat_currency_id: UUID
    crypto_currency_id: UUID
    type: str  
    price: float
    network_ids: List[UUID]  
    
class OfferUpdateSchema(BaseModel):
    price: Optional[float] = None
    is_active: Optional[bool] = None
    network_ids: Optional[List[UUID]] = None

class OfferSchema(BaseModel):
    id: UUID
    arbitrator_id: UUID
    fiat_currency_id: UUID
    crypto_currency_id: UUID
    type: str
    price: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    networks: List[NetworkSchema]

    class Config:
        orm_mode = True

class DealSchema(BaseModel):
    id: UUID
    buyer_id: UUID
    arbitrator_id: Optional[UUID]
    arbitrator_offer_id: Optional[UUID]
    fiat_currency_id: UUID
    crypto_currency_id: UUID
    fiat_amount: float
    crypto_amount: float
    bank_id: Optional[UUID]
    network_id: Optional[UUID]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class StatisticsSchema(BaseModel):
    total_deals: int
    total_fiat: float
    total_crypto: float