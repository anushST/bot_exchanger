from enum import Enum
from typing import Optional

from pydantic import BaseModel


class EmergencyChoices(Enum):
    EXCHANGE = 'EXCHANGE'
    REFUND = 'REFUND'


class CreateEmergency(BaseModel):
    id: str
    token: str
    choice: EmergencyChoices
    address: Optional[str] = None
    tag: Optional[str] = None
