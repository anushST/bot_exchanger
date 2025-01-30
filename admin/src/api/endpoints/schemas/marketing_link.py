from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MarketingLinkCreate(BaseModel):
    name: str


class MarketingLinkUpdate(BaseModel):
    name: Optional[str] = None


class MarketingLinkOut(BaseModel):
    id: UUID
    name: str
    new_users: int
    total_clicks: int
    link: str

    model_config = ConfigDict(
        from_attributes=True
    )
