from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ARBITRATOR = "ARBITRATOR"
