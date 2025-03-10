from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_async_session
from src.models import User
from src.exceptions import ExpiredSignatureError, InvalidTokenError
from src.enums import UserRole
from src.utils import decode_token

router = APIRouter()


async def get_current_user(
        token: str = Depends(OAuth2PasswordBearer(
            tokenUrl='http://localhost:8002/api/v1/auth/login/swagger')),
        session: AsyncSession = Depends(get_async_session)):
    credentials_exception = HTTPException(
        status_code=401,
        detail='Could not validate credentials'
    )
    try:
        payload = decode_token(token)
        user_id = payload.get('user_id')
        if not user_id:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token is expired')
    except InvalidTokenError:
        raise credentials_exception

    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalars().first()
    if not user:
        raise credentials_exception

    if not user.is_email_confirmed:
        raise HTTPException(status_code=403, detail='Email is not confirmed')

    if not user.is_active:
        raise HTTPException(status_code=403, detail='User is inactive')

    user.last_active_at = datetime.now()
    await session.commit()
    await session.refresh(user)
    return user


async def get_arbitrager(user: User = Depends(get_current_user)):
    if user.arbitrager and user.role == UserRole.ARBITRAGER.value:
        return user.arbitrager
    raise HTTPException(
        403, 'You are not arbitrager, please become arbitrager')
