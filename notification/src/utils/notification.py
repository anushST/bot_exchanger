from pydantic import BaseModel, UUID4

from src.kafka import kafka_producer


class NotificationMessage(BaseModel):
    user_id: UUID4
    message: str
    timestamp: str  # Формат ISO 8601


async def send_notification(topic: str, data: dict):
    """Преобразует данные в строгий JSON, проверяет и отправляет в Kafka"""
    try:
        message = NotificationMessage(**data)
        json_data = message.model_dump_json()
        await kafka_producer.send_and_wait(
            topic, value=json_data.encode('utf-8'))
    except Exception as e:
        print(f"Ошибка валидации JSON: {e}")
