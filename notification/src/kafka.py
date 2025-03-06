import asyncio
import json

from aiokafka import AIOKafkaProducer

# from src.core.config import setting

kafka_producer = None


async def init_kafka():
    global kafka_producer
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )


async def send_message():
    await init_kafka()
    await kafka_producer.start()
    try:
        message = {"user_id": 1, "message": "Hello Kafka!"}
        await kafka_producer.send_and_wait("notifications", value=message)
        print("Message sent!")
    finally:
        await kafka_producer.stop()

asyncio.run(send_message())
