from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.api.v1.schemas import UserResponse, UserUpdate
from src.core.db import get_async_session
from src.enums import UserRole
from src.models import User, Arbitrager
from src.exceptions import ExpiredSignatureError, InvalidTokenError
from src.utils import decode_token

router = APIRouter()


async def get_current_user(
        token: str = Depends(OAuth2PasswordBearer(
            tokenUrl='/api/v1/auth/login/swagger')),
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


@router.patch('/become-arbitrager', tags=['User'])
async def become_arbitrager(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        user.role = UserRole.ARBITRAGER.value
        session.add(user)
        await session.commit()
        await session.refresh(user)

        arbitrager = Arbitrager(user_id=user.id)
        session.add(arbitrager)
        await session.commit()
        await session.refresh(arbitrager)

        return {'detail': 'You are succesfully became an arbitrager'}
    except IntegrityError:
        raise HTTPException(400, 'You are already an arbitrager')


@router.get("/me", response_model=UserResponse, tags=['User'])
def get_me(user: User = Depends(get_current_user)):
    return UserResponse(
        email=user.email, full_name=user.full_name,
        tg_id=user.tg_id, is_email_confirmed=user.is_email_confirmed,
        is_active=user.is_active)


@router.put("/update", response_model=UserResponse, tags=['User'])
async def update_user(
        user_update: UserUpdate,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)
) -> UserResponse:
    user.full_name = user_update.full_name
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserResponse(
        email=user.email, full_name=user.full_name,
        tg_id=user.tg_id, is_email_confirmed=user.is_email_confirmed,
        is_active=user.is_active)
