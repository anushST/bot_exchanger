import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from src.core.config import settings
from src.exceptions import ExpiredSignatureError, InvalidTokenError

ALGORITHM = "HS256"
ACCESS_EXPIRE_MINUTES = 15
REFRESH_EXPIRE_MINUTES = 30 * 24 * 60
MAIL_EXPIRE_MINUTES = 15


def create_mail_token(
    mail: str, expire: Optional[int] = MAIL_EXPIRE_MINUTES
) -> str:
    access_payload = {
        "email": mail,
        "salt": str(uuid.uuid4()),
    }
    if expire:
        access_payload.update(
            exp=datetime.now(tz=timezone.utc) + timedelta(minutes=expire)
        )
    return jwt.encode(access_payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_token(
        user_id: uuid.UUID,
        expire: Optional[int] = None
) -> str:
    access_payload = {
        "user_id": str(user_id),
        "salt": str(uuid.uuid4()),
    }
    if expire:
        access_payload.update(
            exp=datetime.now(tz=timezone.utc) + timedelta(minutes=expire)
        )
    return jwt.encode(access_payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_tokens(
        user_id: uuid.UUID,
        access_expire: Optional[timedelta] = ACCESS_EXPIRE_MINUTES,
        refresh_expire: Optional[timedelta] = REFRESH_EXPIRE_MINUTES
) -> tuple:
    access_token = create_token(user_id, access_expire)
    refresh_token = create_token(user_id, refresh_expire)

    return access_token, refresh_token


def refresh_access_token(refresh_token: str) -> str:
    refresh_payload = decode_token(refresh_token)
    user_id = refresh_payload.get('user_id')
    if not user_id:
        raise ValueError('User ID is not found in the token.')
    return create_token(user_id, ACCESS_EXPIRE_MINUTES)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY,
                          algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ExpiredSignatureError('Token is expired.')
    except jwt.InvalidTokenError:
        raise InvalidTokenError('Token is invalid.')
