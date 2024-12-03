import importlib
from src.database import Base

MODELS = ['currency', 'exchange', 'exchanger', 'exchanger_currency', 'user']

def init_models(db):
    for router in MODELS:
        importlib.import_module("." + router, package=__name__)
    Base.metadata.create_all(db)
