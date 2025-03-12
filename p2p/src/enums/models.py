from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ARBITRAGER = "ARBITRAGER"


class ModerationStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class CurrencyType(str, Enum):
    FIAT = "FIAT"
    CRYPTO = "CRYPTO"


class DealStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    MODERATION = "MODERATION"


class MessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"


class OfferType(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'
