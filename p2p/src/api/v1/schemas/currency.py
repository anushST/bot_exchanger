from typing import Optional

from pydantic import BaseModel, UUID4, ConfigDict

from .network import NetworkResponse
from src.enums import CurrencyType


class CurrencyBase(BaseModel):
    name: str
    code: str
    type: CurrencyType


class CurrencyCreate(CurrencyBase):
    is_active: Optional[bool] = True
    network_ids: list[UUID4]


class CurrencyUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    type: Optional[CurrencyType] = None
    is_active: Optional[bool] = None
    network_ids: Optional[list[UUID4]] = None


class CurrencyResponse(CurrencyBase):
    id: UUID4
    networks: list[NetworkResponse]

    model_config = ConfigDict(
        from_attributes=True
    )
