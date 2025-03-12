import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.message import MessageCreate, MessageRead
from src.models import User, ChatMessage
from src.core.db import get_async_session
from src.api.v1.services.message import (
    create_message, get_messages_by_deal, mark_message_read)
from src.utils import get_current_user

router = APIRouter()


@router.post("/", response_model=MessageRead)
async def send_message(
    message: MessageCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user)
):
    # media_url = None
    # media_type = None

    # if media:
    #     # тут логика сохранения файла, например, в S3 или локально
    #     # сохраняем и получаем media_url
    #     saved_path = f"/some/path/{media.filename}"  # пример
    #     media_url = saved_path
    #     # определяем тип в зависимости от расширения или внешних данных
    #     media_type = "photo"  # или "video"/"audio"

    # message_data = MessageCreate(
    #     deal_id=deal_id,
    #     text=text,
    #     media_url=media_url,
    #     media_type=media_type
    # )

    new_message = await create_message(
        db, message, sender_id=user.id)
    return new_message


@router.get('/{deal_id}', response_model=list[MessageRead])
async def get_deal_messages(
    deal_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user),
):
    messages = await get_messages_by_deal(session, deal_id, user.id)

    if not messages:
        raise HTTPException(status_code=404, detail='Deal not found')
    return messages


@router.patch("/{message_id}/read", response_model=MessageRead)
async def mark_as_read(
    message_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user)
):
    query = select(ChatMessage).where(ChatMessage.id == message_id)
    result = await session.execute(query)
    msg_obj = result.scalars().first()

    not_found = HTTPException(404, 'Message not found')

    if not msg_obj:
        raise not_found

    if not msg_obj.deal:
        raise not_found

    is_buyer = msg_obj.deal.buyer_id == user.id
    is_arbitrager = msg_obj.deal.offer.arbitrager.user.id == user.id

    if not (is_buyer or is_arbitrager):
        raise not_found

    if msg_obj.is_read:
        raise HTTPException(400, 'Message already read')

    if msg_obj.sender_id == user.id:
        raise HTTPException(400, 'You can not read your message')

    msg_obj.is_read = True
    await session.commit()
    await session.refresh(msg_obj)

    return msg_obj
