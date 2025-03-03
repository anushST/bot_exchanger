from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.messages import Message
from app.schemas.messages import MessageCreate, MessageRead
from typing import List

async def create_message(db: AsyncSession, message_data: MessageCreate, sender_id: int) -> MessageRead:
    new_message = Message(
        deal_id=message_data.deal_id,
        sender_id=sender_id,
        text=message_data.text,
        media_url=message_data.media_url,
        media_type=message_data.media_type
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    return new_message


async def get_messages_by_deal(db: AsyncSession, deal_id: int) -> List[MessageRead]:
    query = select(Message).where(Message.deal_id == deal_id).order_by(Message.created_at.asc())
    result = await db.execute(query)
    messages = result.scalars().all()
    return [MessageRead.from_orm(m) for m in messages]


async def mark_message_read(db: AsyncSession, message_id: int) -> MessageRead:
    query = select(Message).where(Message.id == message_id)
    result = await db.execute(query)
    msg_obj = result.scalar_one_or_none()
    
    if msg_obj is None:
        # Можно вернуть ошибку или исключение
        # raise HTTPException(status_code=404, detail="Message not found")
        pass
    
    msg_obj.is_read = True
    db.add(msg_obj)
    await db.commit()
    await db.refresh(msg_obj)
    return MessageRead.from_orm(msg_obj)
