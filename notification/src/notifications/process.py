import json
import logging
from aiokafka import AIOKafkaConsumer

from src.core.config import settings
from src.utils import NotificationMessage

logger = logging.getLogger(__name__)

KAFKA_TOPIC = "notifications"


async def consume():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVICE,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    await consumer.start()
    try:
        logger.info("Notification service started listening...")
        async for msg in consumer:
            data = json.loads(msg.value.decode("utf-8"))
            logger.info(f"Received message: {data}")
            data = NotificationMessage(**data)
            await process_notification(data)
    finally:
        await consumer.stop()


async def process_notification(data: NotificationMessage):
    logger.info(f"Processing notification: {data}")
