from enum import Enum


class Exchangers(Enum):
    FFIO = 'ffio'
    CHANGELLY = 'changelly'
    EASYBIT = 'eastbit'


class RateLoadedExchangers(Enum):
    FFIO = 'ffio'
    EASYBIT = 'eastbit'
