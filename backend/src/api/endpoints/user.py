from fastapi import APIRouter, Depends

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_async_session
from src.models import User

router = APIRouter()


@router.get('/')
async def get_users(db: AsyncSession = Depends(get_async_session)):
    stmt = select(User)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return users
