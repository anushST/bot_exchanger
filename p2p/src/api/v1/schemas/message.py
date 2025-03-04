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
    text: Optional[str]
    media_url: Optional[str]
    media_type: Optional[str]
    is_read: bool

    model_config = ConfigDict(
        from_attributes=True
    )
