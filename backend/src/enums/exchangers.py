from enum import Enum


class Exchangers(Enum):
    FFIO = 'ffio'
    CHANGELLY = 'changelly'
    EASTBIT = 'eastbit'


class RateLoadedExchangers(Enum):
    FFIO = 'ffio'
    EASTBIT = 'eastbit'