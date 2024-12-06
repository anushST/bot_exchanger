from .db import DataBaseMiddleware
from .user import UserMiddleware

def init_middlewares(dispatcher, session):
    dispatcher.message.outer_middleware(DataBaseMiddleware(session))
    dispatcher.callback_query.outer_middleware(DataBaseMiddleware(session))

    dispatcher.message.outer_middleware(UserMiddleware())
    dispatcher.callback_query.outer_middleware(UserMiddleware())