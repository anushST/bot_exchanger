import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.message import MessageCreate, MessageRead
from src.enums import UserRole
from src.models import Appeal, Arbitrager, Deal, Offer, User, ChatMessage
from src.core.db import get_async_session
from src.utils import get_current_user

router = APIRouter()


async def get_deal(session: AsyncSession, deal_id, user_id):
    result = await session.execute(
            select(Deal)
            .where(
                (Deal.id == deal_id) &
                ((Deal.buyer_id == user_id) |
                 (Deal.offer.has(
                     Offer.arbitrager.has(Arbitrager.user_id == user_id))))
            )
            .options(joinedload(Deal.offer).joinedload(Offer.arbitrager))
        )
    deal = result.scalars().first()
    return deal


@router.post("/", response_model=MessageRead)
async def send_message(
    message: MessageCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user)
):
    deal = await get_deal(session, message.deal_id, user.id)

    if user.role == UserRole.MODERATOR.value:
        result = await session.execute(
            select(Deal).where(Deal.id == message.deal_id))
        deal = result.scalars().first()

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    new_message = ChatMessage(
        deal_id=deal.id,
        sender_id=user.id,
        message_content=message.text,
    )
    if user.role == UserRole.MODERATOR.value:
        new_message.is_from_moderator = True

    session.add(new_message)
    await session.commit()
    await session.refresh(new_message)
    return new_message


@router.get('/{deal_id}', response_model=list[MessageRead])
async def get_deal_messages(
    deal_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user),
):
    deal = await get_deal(session, deal_id, user.id)

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    query = select(ChatMessage).where(
        ChatMessage.deal_id == deal_id).order_by(
            ChatMessage.created_at.asc())
    result = await session.execute(query)
    messages = result.unique().scalars().all()
    return [MessageRead.model_validate(m) for m in messages]


@router.get('/appeal/{appeal_id}', response_model=list[MessageRead])
async def get_appeal_messages(
    appeal_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user),
):
    query = select(Appeal).where(Appeal.id == appeal_id)
    result = await session.execute(query)
    appeal = result.scalars().first()

    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")

    query = select(ChatMessage).where(
        ChatMessage.deal_id == appeal.deal_id).order_by(
            ChatMessage.created_at.asc())
    result = await session.execute(query)
    messages = result.unique().scalars().all()
    return [MessageRead.model_validate(m) for m in messages]


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
