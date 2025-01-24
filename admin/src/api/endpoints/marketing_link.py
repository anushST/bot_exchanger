from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select

from src.core.db import get_async_session
from src.core.config import settings
from src.models import MarketingLink, User

from .schemas import (
    MarketingLinkCreate,
    MarketingLinkUpdate,
    MarketingLinkOut
)

router = APIRouter()


@router.get("/", response_model=list[MarketingLinkOut])
async def get_marketing_links(
    user_id: int = None,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Получить все маркетинговые ссылки.
    Необязательный параметр user (имя пользователя).
    Если он передан — фильтруем по user_name.
    """
    stmt = select(MarketingLink)
    if user_id:
        stmt = (
            select(MarketingLink)
            .join(MarketingLink.user)
            .where(User.tg_id == user_id)
        )
    result = await db.execute(stmt)
    links = result.scalars().all()
    result = []
    if links:
        for link in links:
            result.append(MarketingLinkOut(
                id=link.id,
                name=link.name,
                user_id=link.user.tg_id,
                new_users=link.new_users,
                total_clicks=link.total_clicks,
                link=f"https://{settings.DOMAIN}/lk/{link.id}"
            ))
    return result


@router.get("/{link_id}", response_model=MarketingLinkOut)
async def get_marketing_link(
    link_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Получить конкретную маркетинговую ссылку по её UUID.
    """
    stmt = select(MarketingLink).where(MarketingLink.id == link_id)
    result = await db.execute(stmt)
    marketing_link = result.scalars().first()
    if not marketing_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Marketing link not found"
        )
    return marketing_link


@router.post("/", response_model=MarketingLinkOut,
             status_code=status.HTTP_201_CREATED)
async def create_marketing_link(
    data: MarketingLinkCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Создать маркетинговую ссылку.
    - user_name: имя пользователя (строка).
    - name: название ссылки (строка).
    """
    stmt_user = select(User).where(User.tg_id == data.user_id)
    user_result = await db.execute(stmt_user)
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this id does not exist"
        )

    stmt_link = select(MarketingLink).where(MarketingLink.name == data.name)
    link_result = await db.execute(stmt_link)
    existing_link = link_result.scalars().first()
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link with this name already exists"
        )

    new_link = MarketingLink(
        name=data.name,
        user_id=user.id
    )
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return MarketingLinkOut(
        id=new_link.id,
        name=new_link.name,
        user_id=new_link.user.tg_id,
        new_users=new_link.new_users,
        total_clicks=new_link.total_clicks,
        link=f"https://{settings.DOMAIN}/lk/{new_link.id}"
    )


@router.patch("/{link_id}", response_model=MarketingLinkOut)
async def update_marketing_link(
    link_id: UUID,
    data: MarketingLinkUpdate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Обновить только название маркетинговой ссылки (по UUID).
    """
    stmt = select(MarketingLink).where(MarketingLink.id == link_id)
    result = await db.execute(stmt)
    marketing_link = result.scalars().first()

    if not marketing_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Marketing link not found"
        )

    if data.name is not None:
        stmt_check = select(MarketingLink).where(
            MarketingLink.name == data.name)
        check_result = await db.execute(stmt_check)
        existing_link = check_result.scalars().first()

        if existing_link and existing_link.id != link_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Link with this name already exists"
            )
        marketing_link.name = data.name

    await db.commit()
    await db.refresh(marketing_link)
    return marketing_link


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_marketing_link(
    link_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Удалить маркетинговую ссылку по её UUID.
    """
    stmt = select(MarketingLink).where(MarketingLink.id == link_id)
    result = await db.execute(stmt)
    marketing_link = result.scalars().first()

    if not marketing_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Marketing link not found"
        )

    await db.delete(marketing_link)
    await db.commit()
    return None
