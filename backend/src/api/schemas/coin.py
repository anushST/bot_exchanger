from typing import Optional

from pydantic import BaseModel


class Coin(BaseModel):
    code: Optional[str] = None
    coin: Optional[str] = None
    network: Optional[str] = None
    receive: Optional[bool] = None
    send: Optional[bool] = None
    tag_name: Optional[str] = None
