from enum import Enum


class Exchangers(Enum):
    FFIO = 'ffio'
    CHANGELLY = 'changelly'


class RateLoadedExchangers(Enum):
    FFIO = 'ffio'
