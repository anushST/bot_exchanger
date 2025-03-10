import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from aiokafka import AIOKafkaProducer

from pydantic import BaseModel, UUID4

NOTIFICATION_TOPIK = 'notifications'


class NotificationMessage(BaseModel):
    user_id: UUID4
    code: int
    data: dict
    timestamp: Optional[int] = int(datetime.now(timezone.utc).timestamp())


async def send_notification(user_id: uuid.UUID, code: int, data: dict):
    try:
        message = NotificationMessage(
            user_id=user_id, code=code, data=data
        )
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers='localhost:9092',
        )
        json_data = message.model_dump_json()
        await kafka_producer.start()
        try:
            await kafka_producer.send_and_wait(
                NOTIFICATION_TOPIK, value=json_data.encode('utf-8'))
        finally:
            await kafka_producer.stop()
    except Exception as e:
        print(f"Ошибка валидации JSON: {e}")
        raise
