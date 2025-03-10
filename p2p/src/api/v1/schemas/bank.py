from typing import Optional

from pydantic import BaseModel, ConfigDict, UUID4


class BankBase(BaseModel):
    name: str
    code: str
    country: str


class BankCreate(BankBase):
    is_active: Optional[bool] = True


class BankUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None


class BankResponse(BankBase):
    id: UUID4

    model_config = ConfigDict(
        from_attributes=True
    )
