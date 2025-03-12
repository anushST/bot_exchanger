from datetime import datetime

from pydantic import BaseModel, ConfigDict, UUID4
from typing import Optional


class MessageBase(BaseModel):
    deal_id: UUID4
    text: Optional[str] = None


class MessageCreate(MessageBase):
    pass


class MessageRead(BaseModel):
    id: UUID4
    deal_id: UUID4
    message_content: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
