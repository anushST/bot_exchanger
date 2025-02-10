from typing import Optional

from pydantic import BaseModel


class Coin(BaseModel):
    code: str
    coin: str
    network: str
    receive: bool
    send: bool
    tag_name: Optional[str] = None
