from redis.asyncio import Redis

from src.core.config import settings

redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DATABASE,
            decode_responses=True
        )
