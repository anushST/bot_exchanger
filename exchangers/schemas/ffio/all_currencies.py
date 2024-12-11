from pydantic import BaseModel, HttpUrl
from typing import List, Optional


class Currency(BaseModel):
    code: str
    coin: str
    network: str
    name: str
    recv: bool
    send: bool
    tag: Optional[str]
    logo: HttpUrl
    color: str
    priority: int
