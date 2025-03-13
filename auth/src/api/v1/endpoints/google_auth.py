from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1 import schemas
from src.core.config import settings
from src.core.db import get_async_session
from src.models import User
from src.utils import create_tokens

router = APIRouter()


oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params={'scope': 'openid email profile'},
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs"
)


@router.get('/google-callback', response_model=schemas.TokensResponse)
async def auth_callback(
    token: str, session: AsyncSession = Depends(get_async_session)
):
    try:
        user_info = await oauth.google.get(
            "https://openidconnect.googleapis.com/v1/userinfo", token=token)
        user_info: dict = user_info.json()
    except Exception:
        raise HTTPException(status_code=400, detail='Auth error')

    email = user_info.get('email')
    name = user_info.get('name', 'user')

    if email:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if not user:
            user = User(email=email, full_name=name, is_email_confirmed=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        tokens = create_tokens(user.id)

        return schemas.TokensResponse(
            access_token=tokens[0], refresh_token=tokens[1]
        )

    raise HTTPException(status_code=400, detail='Email not found')
