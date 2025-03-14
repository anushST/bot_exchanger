
from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from google.oauth2 import id_token
from google.auth.transport import requests

from src.api.v1 import schemas
from src.core.config import settings
from src.core.db import get_async_session
from src.models import User
from src.utils import create_tokens

router = APIRouter()


class Credentials(BaseModel):
    token: str


@router.post('/google-callback', response_model=schemas.TokensResponse)
async def auth_callback(
    credentials: Credentials,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        id_info = id_token.verify_oauth2_token(
            credentials.token, requests.Request(), settings.GOOGLE_CLIENT_ID
        )

        if id_info["aud"] != settings.GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Invalid audience")

        email = id_info.get("email")
        name = id_info.get("name", "Unknown")

        if email:
            result = await session.execute(
                select(User).where(User.email == email))
            user = result.scalars().first()

            if not user:
                user = User(email=email, full_name=name,
                            is_email_confirmed=True)
                session.add(user)
                await session.commit()
                await session.refresh(user)

            tokens = create_tokens(user.id)

            return schemas.TokensResponse(
                access_token=tokens[0], refresh_token=tokens[1]
            )
        raise HTTPException(status_code=400, detail='Email not found')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")
