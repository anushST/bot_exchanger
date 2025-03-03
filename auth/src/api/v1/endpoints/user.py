from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas import UserResponse, UserUpdate
from src.core.db import get_async_session
from src.models import User
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
    return user


@router.get("/me", response_model=UserResponse, tags=['User'])
def get_me(user: User = Depends(get_current_user)):
    return UserResponse(email=user.email, full_name=user.full_name)


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
    return UserResponse(email=user.email, full_name=user.full_name)
