import logging

from redis.asyncio import StrictRedis

from src.config import config
from src.api.ffio import schemas

logger = logging.getLogger(__name__)


class ChangellyRedisClient:
    EXCHANGER = 'changelly'
    COINS_KEY = 'coins'
    COIN_NETWORKS = '{coin_name}:networks'
    FULL_COIN_INFO_KEY = '{exchanger}:{coin_name}:{network}:info'
    RATE_KEY = '{exchanger}:{type}:{from_coin}:to:{to_coin}:info'

    def __init__(self):
        self.redis_client = StrictRedis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DATABASE,
            decode_responses=True
        )

    async def get_coins(self) -> set[str]:
        return await self.redis_client.smembers(self.COINS_KEY)

    async def get_networks(self, coin_name: str) -> set[str]:
        return await self.redis_client.smembers(
            self.COIN_NETWORKS.format(coin_name=coin_name))

    async def get_coin_full_info(self, coin_name: str,
                                 network: str) -> schemas.Currency:
        coin_info = await self.redis_client.get(
            self.FULL_COIN_INFO_KEY.format(
                exchanger=self.EXCHANGER,
                coin_name=coin_name,
                network=network
            )
        )
        import json
        coin_info = json.loads(coin_info)
        return schemas.Currency(
            code=coin_info.get('ticker'),
            coin=coin_info.get('coin').upper(),
            network=coin_info.get('network').upper(),
            name=coin_info.get('name'),
            recv=coin_info.get('enabled_to'),
            send=coin_info.get('enabled_from')
        )


changelly_redis_client = ChangellyRedisClient()
