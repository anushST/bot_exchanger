from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ARBITRAGER = "ARBITRAGER"


class AppealStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class CurrencyType(str, Enum):
    FIAT = "FIAT"
    CRYPTO = "CRYPTO"


class DealStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    APPEAL = "APPEAL"


class MessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"


class OfferType(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'
