from datetime import datetime

from pydantic import BaseModel, ConfigDict, UUID4

from .deal import DealResponse
from .user import UserResponse
from src.enums import AppealStatus


class AppealCreate(BaseModel):
    deal_id: UUID4
    reason: str


class AppealResponse(BaseModel):
    id: UUID4
    deal: DealResponse
    reason: str
    requested_by: UserResponse
    status: AppealStatus
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
