from enum import Enum
from typing import Optional

from pydantic import BaseModel


class EmergencyChoice(Enum):
    NONE = "NONE"
    EXCHANGE = "EXCHANGE"
    REFUND = "REFUND"


class CreateEmergency(BaseModel):
    id: str
    token: str
    choice: EmergencyChoice
    address: Optional[str] = None
    tag: Optional[str] = None
