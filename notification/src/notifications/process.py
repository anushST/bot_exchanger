import json
import logging

from aiokafka import AIOKafkaConsumer
from sqlalchemy import select

from src.core.config import settings
from src.core.db import get_async_session_generator
from src.models import User
from src.utils import NotificationMessage, send_mail

logger = logging.getLogger(__name__)

KAFKA_TOPIC = "notifications"


async def consume():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVICE,
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
    await consumer.start()
    try:
        logger.info("Notification service started listening...")
        async for msg in consumer:
            try:
                data = json.loads(msg.value.decode("utf-8"))
                logger.info(f"Received message: {data}")
                data = NotificationMessage(**data)
                await process_notification(data)
            except Exception:
                raise
    finally:
        await consumer.stop()


async def process_notification(data: NotificationMessage):
    async with get_async_session_generator() as session:
        result = await session.execute(select(User).where(User.id == data.user_id))
        user = result.scalars().first()
        print(user)
        if not user:
            return

    if data.code == 100:  # Email Confirmation
        print('message_sent')
        await send_mail('anushervon.s.06@gmail.com', 'message', 'hithere')
