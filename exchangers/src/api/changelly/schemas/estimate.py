from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CreateFloatEstimate(BaseModel):
    from_coin: str = Field(..., alias='from')
    to_coin: str = Field(..., alias='to')
    amount_from: Decimal = Field(..., alias='amountFrom')

    model_config = {
        "populate_by_name": True,
    }


class CreateFixedEstimate(BaseModel):
    from_coin: str = Field(..., alias='from')
    to_coin: str = Field(..., alias='to')
    amount_from: Optional[Decimal] = Field(None, alias='amountFrom')
    amount_to: Optional[Decimal] = Field(None, alias='amountTo')

    model_config = {
        "populate_by_name": True,
    }


class FloatEstimate(BaseModel):
    from_: str = Field(alias="from")
    to: str
    network_fee: Decimal = Field(alias="networkFee")
    amount_from: Decimal = Field(alias="amountFrom")
    amount_to: Decimal = Field(alias="amountTo")
    max_: Decimal = Field(alias="max")
    max_from: Decimal = Field(alias="maxFrom")
    max_to: Decimal = Field(alias="maxTo")
    min_: Decimal = Field(alias="min")
    min_from: Decimal = Field(alias="minFrom")
    min_to: Decimal = Field(alias="minTo")
    visible_amount: Decimal = Field(alias="visibleAmount")
    rate: Decimal = Field(alias="rate")
    fee: Decimal = Field(alias="fee")


class FixedEstimate(BaseModel):
    id_: str = Field(alias="id")
    from_: str = Field(alias="from")
    to: str
    result: Decimal
    network_fee: Decimal = Field(alias="networkFee")
    max_: Decimal = Field(alias="max")
    max_from: Decimal = Field(alias="maxFrom")
    max_to: Decimal = Field(alias="maxTo")
    min_: Decimal = Field(alias="min")
    min_from: Decimal = Field(alias="minFrom")
    min_to: Decimal = Field(alias="minTo")
    amount_from: Decimal = Field(alias="amountFrom")
    amount_to: Decimal = Field(alias="amountTo")
    expired_at: int = Field(alias="expiredAt")
