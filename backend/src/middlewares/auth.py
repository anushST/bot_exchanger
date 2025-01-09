import hmac
import hashlib

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.future import select

from src.core.config import settings
from src.core.db import get_async_session
from src.models import User


def verify_init_data(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(status_code=400, detail="Missing initData")

    params = dict(item.split('=') for item in init_data.split('&'))
    received_hash = params.pop('hash', None)

    if not received_hash:
        raise HTTPException(status_code=400, detail="Invalid initData format")

    data_check_string = '\n'.join(
        f"{key}={value}" for key, value in sorted(params.items()))
    secret_key = hashlib.sha256(settings.TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(),
                               hashlib.sha256).hexdigest()

    if not hmac.compare_digest(received_hash, calculated_hash):
        raise HTTPException(status_code=403,
                            detail="Invalid initData signature")

    return params


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

        user_id = user_data.get('id')

        async with get_async_session() as session:
            response = await session.execute(
                select(User).where(User.tg_id == user_id)
            )
            user = response.scalars().first()

            if not user:
                user = User(
                    tg_id=user_id,
                    tg_name='hi'
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

        request.state.user = user

        response = await call_next(request)
        return response
