from decimal import Decimal

from pydantic import BaseModel

from src.api.ffio.schemas import OrderType


class CreateBestPrice(BaseModel):
    type: OrderType
    from_currency: str
    to_currency: str
    from_network: str
    to_network: str
    direction: str
    amount: Decimal


class BestPrice(CreateBestPrice):
    exchanger: str
    from_amount: Decimal
    to_amount: Decimal
