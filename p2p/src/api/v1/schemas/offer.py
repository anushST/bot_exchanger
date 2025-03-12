from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, UUID4, ConfigDict

from .arbitrager import ArbitragerResponse
from .bank import BankResponse
from .currency import CurrencyResponse
from .network import NetworkResponse
from src.enums import OfferType


class OfferBase(BaseModel):
    fiat_currency_id: UUID4
    crypto_currency_id: UUID4
    type: OfferType
    price: Decimal


class OfferCreate(OfferBase):
    is_active: bool
    network_ids: list[UUID4]
    bank_ids: list[UUID4]


class OfferUpdate(BaseModel):
    arbitrator_id: Optional[UUID4] = None
    fiat_currency_id: Optional[UUID4] = None
    crypto_currency_id: Optional[UUID4] = None
    type: Optional[OfferType] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    network_ids: Optional[list[UUID4]] = None
    bank_ids: Optional[list[UUID4]] = None


class OfferResponse(OfferBase):
    id: UUID4
    arbitrager: ArbitragerResponse
    fiat_currency: CurrencyResponse
    crypto_currency: CurrencyResponse
    networks: list[NetworkResponse]
    banks: list[BankResponse]

    model_config = ConfigDict(
        from_attributes=True
    )
