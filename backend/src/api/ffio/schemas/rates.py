from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.models import DirectionTypes


class RatesSchema(BaseModel):
    from_coin: str
    to_coin: str = Field(..., alias='to')
    in_amount: Decimal
    out_amount: Decimal = Field(..., alias='out')
    amount: Decimal
    tofee: Optional[Decimal] = None
    tofee_currency: Optional[str] = None
    min_amount: Decimal = Field(..., alias='minamount')
    max_amount: Decimal = Field(..., alias='maxamount')

    # ToDo - fix the bug with incorrect min and max ammounts
    def get_clean_out_amount(self, out_amount) -> Decimal:
        return out_amount - self.tofee

    def calculate_from_amount(self, to_amount: Decimal) -> Decimal:
        diff = self.out_amount / self.in_amount
        return to_amount / diff

    def calculate_to_amount(self, from_amount: Decimal) -> Decimal:
        diff = self.out_amount / self.in_amount
        return self.get_clean_out_amount(from_amount * diff)

    def get_to_min_amount(self) -> Decimal:
        return self.calculate_to_amount(self.min_amount)

    def get_to_max_amount(self) -> Decimal:
        return self.calculate_to_amount(self.max_amount)

    def check_min_max_limits(self, direction: str, amount: Decimal) -> bool:
        if direction == DirectionTypes.FROM:
            if (amount > self.min_amount
                    and amount < self.max_amount and amount > 0):
                return True
        elif direction == DirectionTypes.TO:
            if (amount > self.get_to_min_amount()
                    and amount < self.get_to_max_amount() and amount > 0):
                return True
        else:
            raise Exception('Incorrect direction.')
        return False
