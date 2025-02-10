from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    tg_id: int
    tg_name: str
    tg_username: Optional[str]
