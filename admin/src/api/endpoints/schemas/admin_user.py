from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class AdminUserBase(BaseModel):
    name: str
    is_superuser: bool = False
    is_active: bool = True


class AdminUserCreate(AdminUserBase):
    tg_id: int  # при создании передаём tg_id


class AdminUserUpdate(BaseModel):
    name: Optional[str]
    is_superuser: Optional[bool]
    is_active: Optional[bool]


class AdminUserResponse(AdminUserBase):
    tg_id: int
    last_active_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
