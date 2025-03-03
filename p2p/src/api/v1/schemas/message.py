from pydantic import BaseModel, ConfigDict
from typing import Optional


class MessageBase(BaseModel):
    deal_id: int
    text: Optional[str] = None


class MessageCreate(MessageBase):
    media_url: Optional[str] = None
    media_type: Optional[str] = None


class MessageRead(BaseModel):
    id: int
    deal_id: int
    text: Optional[str]
    media_url: Optional[str]
    media_type: Optional[str]
    is_read: bool

    model_config = ConfigDict(
        orm_mode=True
    )
