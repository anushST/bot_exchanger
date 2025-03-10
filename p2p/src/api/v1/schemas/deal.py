from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, UUID4


class DealBase(BaseModel):
    buyer_id: UUID4
    arbitrator_id: UUID4
    arbitrator_offer_id: UUID4
    fiat_currency_id: UUID4
    crypto_currency_id: UUID4
    fiat_amount: Decimal
    crypto_amount: Decimal
    bank_id: UUID4
    network_id: UUID4
    crypto_address: UUID4
    status: str


class DealCreate(DealBase):
    pass


class DealResponse(DealBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
