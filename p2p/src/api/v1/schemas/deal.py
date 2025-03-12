from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, UUID4

from .bank import BankResponse
from .network import NetworkResponse
from .offer import OfferResponse
from .user import UserResponse
from src.enums import DirectionTypes, DealStatus


class DealCreate(BaseModel):
    arbitrator_offer_id: UUID4
    bank_id: UUID4
    network_id: UUID4
    direction: DirectionTypes
    amount: Decimal


class DealResponse(BaseModel):
    id: UUID4
    fiat_amount: Decimal
    crypto_amount: Decimal
    buyer: UserResponse
    bank: BankResponse
    network: NetworkResponse
    offer: OfferResponse
    status: DealStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
