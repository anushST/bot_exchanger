from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as Session

from .schemas import AdminUserCreate, AdminUserUpdate, AdminUserResponse
from src.core.db import get_async_session
from src.models import AdminUser

router = APIRouter()


@router.get("/", response_model=List[AdminUserResponse])
async def read_admin_users(page: int = 0, limit: int = 100,
                           db: Session = Depends(get_async_session)):
    """
    Получение списка всех админов с пагинацией (page, limit).
    """
    stmt = select(AdminUser).offset(page).limit(limit)
    result = await db.execute(stmt)
    admin_users = result.scalars().all()
    return admin_users


@router.post("/", response_model=AdminUserResponse)
async def create_admin_user(user_in: AdminUserCreate,
                            db: Session = Depends(get_async_session)):
    """
    Создание нового админа.
    """
    stmt = select(AdminUser).where(AdminUser.tg_id == user_in.tg_id)
    existing_user = await db.execute(stmt)
    existing_user = existing_user.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Admin user with this tg_id already exists")

    db_user = AdminUser(
        tg_id=user_in.tg_id,
        name=user_in.name,
        is_superuser=user_in.is_superuser,
        is_active=user_in.is_active,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.get("/{tg_id}", response_model=AdminUserResponse)
async def get_admin_user(tg_id: int, db: Session = Depends(get_async_session)):
    """
    Получить админа по tg_id.
    """
    stmt = select(AdminUser).where(AdminUser.tg_id == tg_id)
    user = await db.execute(stmt)
    user = user.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")
    return user


@router.patch("/{tg_id}", response_model=AdminUserResponse)
async def update_admin_user(tg_id: int, user_in: AdminUserUpdate,
                            db: Session = Depends(get_async_session)):
    """
    Обновить информацию об админе (частично).
    """
    stmt = select(AdminUser).where(AdminUser.tg_id == tg_id)
    db_user = await db.execute(stmt)
    db_user = db_user.scalars().first()

    if not db_user:
        raise HTTPException(status_code=404, detail="Admin user not found")

    if user_in.name is not None:
        db_user.name = user_in.name
    if user_in.is_superuser is not None:
        db_user.is_superuser = user_in.is_superuser
    if user_in.is_active is not None:
        db_user.is_active = user_in.is_active

    # Если нужно трекать «последнюю активность» при апдейте:
    # db_user.last_active_at = datetime.now()

    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.delete("/{tg_id}")
async def delete_admin_user(
        tg_id: int, db: Session = Depends(get_async_session)):
    """
    Удалить админа по tg_id.
    """
    stmt = select(AdminUser).where(AdminUser.tg_id == tg_id)
    db_user = await db.execute(stmt)
    db_user = db_user.scalars().first()

    if not db_user:
        raise HTTPException(status_code=404, detail="Admin user not found")

    await db.delete(db_user)
    await db.commit()
    return {"detail": "Admin user deleted successfully"}
