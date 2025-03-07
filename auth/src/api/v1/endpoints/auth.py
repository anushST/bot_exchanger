from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .google_auth import router as google_router
from .telegram_auth import router as telegram_router
from src.api.v1 import schemas
from src.core.db import get_async_session
from src.exceptions import ExpiredSignatureError, InvalidTokenError
from src.models import User
from src.utils import (refresh_access_token, get_password_hash,
                       verify_password, create_tokens, send_notification)

router = APIRouter()
router.include_router(google_router)
router.include_router(telegram_router)


@router.post("/refresh")
def refresh_token(data: schemas.RefreshRequest):
    try:
        new_access_token = refresh_access_token(data.refresh_token)
        return {"access_token": new_access_token}
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/signup", response_model=schemas.UserResponse, tags=["Auth"])
async def register_user(
        user_data: schemas.UserCreate,
        session: AsyncSession = Depends(get_async_session)
) -> schemas.UserResponse:
    query = select(User).where(User.email == user_data.email)
    result = await session.execute(query)
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=400,
            detail='User with this email already exists'
        )
    user = User(
        email=user_data.email,
        password=get_password_hash(user_data.password),
        full_name=user_data.full_name
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    await send_notification(user.id, code=100, data={
        'url': 'https://'
    })
    return schemas.UserResponse(
        email=user.email, full_name=user.full_name,
        tg_id=user.tg_id, is_email_confirmed=user.is_email_confirmed,
        is_active=user.is_active)


@router.post("/login/swagger", response_model=schemas.TokensResponse,
             tags=["Auth"])
async def login_swagger(data: OAuth2PasswordRequestForm = Depends(),
                        session: AsyncSession = Depends(get_async_session)):
    stmt = select(User).where(User.email == data.username)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    tokens = create_tokens(user.id)

    return schemas.TokensResponse(
        access_token=tokens[0], refresh_token=tokens[1]
    )


@router.post("/login", response_model=schemas.TokensResponse, tags=["Auth"])
async def login(data: schemas.CreateLogin,
                session: AsyncSession = Depends(get_async_session)):
    stmt = select(User).where(User.email == data.username)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    tokens = create_tokens(user.id)

    return schemas.TokensResponse(
        access_token=tokens[0], refresh_token=tokens[1]
    )
