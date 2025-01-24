import hmac
import hashlib

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.future import select

from src.core.config import settings
from src.core.db import get_async_session_generator
from src.models import User

import logging
from init_data_py import InitData

logger = logging.getLogger(__name__)


def verify_init_data(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(status_code=400, detail="Missing initData")

    in_data = InitData.parse(init_data)

    try:
        if not in_data.validate(settings.TOKEN, lifetime=3600):
            raise HTTPException(status_code=403,
                                detail="Invalid initData signature")
    except Exception:
        raise HTTPException(status_code=403,
                            detail="Invalid initData signature")

    return in_data.to_dict()


class TelegramAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        init_data = (request.query_params.get('initData')
                     or request.headers.get('X-Telegram-InitData'))

        try:
            user_data = verify_init_data(init_data)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={'error': "Missing auth header"})

        user_id = user_data['user'].get('id')

        async with get_async_session_generator() as session:
            response = await session.execute(
                select(User).where(User.tg_id == user_id)
            )
            user = response.scalars().first()

            if not user:
                user = User(
                    tg_id=user_id,
                    tg_name=user_data['user']['first_name']
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

        request.state.user = user

        response = await call_next(request)
        return response
