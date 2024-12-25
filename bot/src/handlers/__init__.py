import importlib

HANDLERS = ["start", "faq", 'exchange', 'inline_handler', 'emergency']


def init_handlers(dispatcher):
    for router in HANDLERS:
        dispatcher.include_router(importlib.import_module("." + router, package=__name__).router)