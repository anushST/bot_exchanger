from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MarketingLinkCreate(BaseModel):
    user_id: int
    name: str


class MarketingLinkUpdate(BaseModel):
    name: Optional[str] = None


class MarketingLinkOut(BaseModel):
    id: UUID
    name: str
    user_id: int
    new_users: int
    total_clicks: int
    link: str

    model_config = ConfigDict(
        from_attributes=True
    )
