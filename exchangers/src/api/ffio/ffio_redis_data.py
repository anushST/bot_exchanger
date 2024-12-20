import logging

from redis.asyncio import StrictRedis

from src.config import config
from src.api.ffio import schemas

logger = logging.getLogger(__name__)


class FFIORedisClient:
    EXCHANGER = 'ffio'
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
        return schemas.Currency.model_validate_json(coin_info)

    async def _get_rate(
            self, rate_type: str, from_coin: str, from_coin_network: str,
            to_coin: str, to_coin_network: str) -> schemas.RatesSchema | None:
        from_coin_info = await self.get_coin_full_info(from_coin,
                                                       from_coin_network)
        to_coin_info = await self.get_coin_full_info(to_coin,
                                                     to_coin_network)

        rate = await self.redis_client.get(
            self.RATE_KEY.format(
                exchanger=self.EXCHANGER,
                type=rate_type,
                from_coin=from_coin_info.code,
                to_coin=to_coin_info.code
            )
        )
        return schemas.RatesSchema.model_validate_json(rate) if rate else None

    async def get_fixed_rate(
            self, from_coin: str, from_coin_network: str,
            to_coin: str, to_coin_network: str) -> schemas.RatesSchema | None:
        return await self._get_rate('fixed', from_coin, from_coin_network,
                                    to_coin, to_coin_network)

    async def get_flaot_rate(
            self, from_coin: str, from_coin_network: str,
            to_coin: str, to_coin_network: str) -> schemas.RatesSchema | None:
        return await self._get_rate('float', from_coin, from_coin_network,
                                    to_coin, to_coin_network)


ffio_redis_client = FFIORedisClient()
