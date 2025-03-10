from typing import Optional

from pydantic import BaseModel, ConfigDict, UUID4


class NetworkBase(BaseModel):
    name: str
    code: str


class NetworkCreate(NetworkBase):
    is_active: Optional[bool] = True


class NetworkUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None


class NetworkResponse(NetworkBase):
    id: UUID4

    model_config = ConfigDict(
        from_attributes=True
    )
