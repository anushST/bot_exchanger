from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1 import schemas
from src.core.config import settings
from src.core.db import get_async_session
from src.models import User
from src.utils import create_tokens, verify_telegram_auth

router = APIRouter()


@router.post('/telegram-auth', response_model=schemas.TokensResponse)
async def auth_check(tg_data: schemas.TelegramAuthRequest,
                     session: AsyncSession = Depends(get_async_session)
                     ) -> schemas.TokensResponse:
    data = tg_data.model_dump(exclude_none=True)
    if not verify_telegram_auth(data, settings.TELEGRAM_BOT_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")

    tg_user_id = int(data.get('id'))

    query = select(User).where(User.tg_id == tg_user_id)
    result = await session.execute(query)
    user = result.scalars().first()

    if not user:
        user = User(
            tg_id=tg_user_id, full_name=data.get('first_name'),
            is_email_confirmed=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    tokens = create_tokens(user.id)

    return schemas.TokensResponse(
        access_token=tokens[0], refresh_token=tokens[1]
    )
