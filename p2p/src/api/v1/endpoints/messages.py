from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from p2p.src.api.v1.schemas.message import MessageCreate, MessageRead
from src.models.messages import Message
from src.core.db import get_async_session
from app.services.message_service import create_message, get_messages_by_deal, mark_message_read

router = APIRouter(
    prefix="/messages",
    tags=["messages"]
)

@router.post("/", response_model=MessageRead)
async def send_message(
    deal_id: int = Form(...),
    text: Optional[str] = Form(None),
    media: Optional[UploadFile] = File(None),  # если хотим загрузку файла
    db: AsyncSession = Depends(async_session_maker),
    current_user_id: int = 1  # заглушка, в реальном случае брать из токена
):
    """
    Отправка сообщения. 
    - text (опционально)
    - media (опционально)
    """
    media_url = None
    media_type = None

    if media:
        # тут логика сохранения файла, например, в S3 или локально
        # сохраняем и получаем media_url
        saved_path = f"/some/path/{media.filename}"  # пример
        media_url = saved_path
        # определяем тип в зависимости от расширения или внешних данных
        media_type = "photo"  # или "video"/"audio"

    message_data = MessageCreate(
        deal_id=deal_id,
        text=text,
        media_url=media_url,
        media_type=media_type
    )
    
    new_message = await create_message(db, message_data, sender_id=current_user_id)
    return new_message


@router.get("/{deal_id}", response_model=List[MessageRead])
async def get_deal_messages(
    deal_id: int,
    db: AsyncSession = Depends(async_session_maker),
    current_user_id: int = 1
):
    """Получить все сообщения по конкретной сделке."""
    messages = await get_messages_by_deal(db, deal_id)
    return messages


@router.patch("/{message_id}/read", response_model=MessageRead)
async def mark_as_read(
    message_id: int,
    db: AsyncSession = Depends(async_session_maker),
    current_user_id: int = 1
):
    """Отметить сообщение прочитанным."""
    updated_msg = await mark_message_read(db, message_id)
    return updated_msg
