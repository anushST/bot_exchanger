from enum import Enum


class Exchangers(Enum):
    FFIO = 'ffio'
    CHANGELLY = 'changelly'
    EASYBIT = 'easybit'


class RateLoadedExchangers(Enum):
    FFIO = 'ffio'
    EASYBIT = 'easybit'