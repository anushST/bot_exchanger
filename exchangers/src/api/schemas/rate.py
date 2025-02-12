from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class RatesSchema(BaseModel):
    from_coin: str
    to_coin: str
    in_amount: Decimal
    out_amount: Decimal
    to_network_fee: Optional[Decimal] = None
    min_from_amount: Optional[Decimal] = None
    min_to_amount: Optional[Decimal] = None
    max_from_amount: Optional[Decimal] = None
    max_to_amount: Optional[Decimal] = None
    set_at: datetime = Field(default_factory=datetime.now, exclude=True)

    def validate_set_at(self) -> bool:
        """Проверяем, что set_at не старше 10 минут"""
        if self.set_at < datetime.now() - timedelta(minutes=10):
            raise False
        return True
