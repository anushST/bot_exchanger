import uuid

from src.api.v1.schemas import MessageCreate, MessageRead
from src.models import ChatMessage, Deal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def create_message(session: AsyncSession, message_data: MessageCreate,
                         sender_id: uuid.UUID) -> MessageRead:
    new_message = ChatMessage(
        deal_id=message_data.deal_id,
        sender_id=sender_id,
        message_content=message_data.text,
        # media_url=message_data.media_url,
        # media_type=message_data.media_type
    )
    session.add(new_message)
    await session.commit()
    await session.refresh(new_message)
    return new_message


async def get_messages_by_deal(
        session: AsyncSession, deal_id: uuid.UUID,
        user_id: uuid.UUID) -> list[MessageRead]:
    deal = await session.execute(select(Deal).where(Deal.id == deal_id))
    deal = deal.scalars().first()

    if deal and (deal.buyer_id == user_id or
                 deal.offer.arbitrager.user.id == user_id):
        query = select(ChatMessage).where(
            ChatMessage.deal_id == deal_id).order_by(
                ChatMessage.created_at.asc())
        result = await session.execute(query)
        messages = result.unique().scalars().all()
        return [MessageRead.model_validate(m) for m in messages]
    return []


async def mark_message_read(
    session: AsyncSession, message_id: uuid.UUID, user_id: uuid.UUID
) -> MessageRead | None:
    query = select(ChatMessage).where(ChatMessage.id == message_id)
    result = await session.execute(query)
    msg_obj = result.scalars().first()

    if (not msg_obj) or msg_obj.deal:
        return None

    is_buyer = msg_obj.deal.buyer_id == user_id
    is_arbitrager = msg_obj.deal.arbitrator_id == user_id

    if (is_buyer or is_arbitrager) and msg_obj.sender_id != user_id:
        msg_obj.is_read = True
        await session.commit()
        await session.refresh(msg_obj)

    return MessageRead.model_validate(msg_obj)
