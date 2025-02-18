import logging
from redis.exceptions import RedisError

from src.api.easybit import schemas
from src.api.schemas import Coin
from src.redis import redis_client

logger = logging.getLogger(__name__)


class EasybitRedisClient:
    EXCHANGER = 'easybit'
    COINS_KEY = 'easybit:coins'
    COIN_NETWORKS = 'easybit:{coin}:networks'
    FULL_COIN_INFO_KEY = 'easybit:{coin}:{network}:info'
    RATE_KEY = 'easybit:rate:{from_coin}:to:{to_coin}:info'

    async def get_coins(self) -> set[str] | None:
        """Получить множество доступных монет."""
        try:
            return await redis_client.smembers(self.COINS_KEY)
        except RedisError as e:
            logger.error('Error fetching coin list: %s', e, exc_info=True)

    async def get_networks(self, coin: str) -> set[str] | None:
        """Получить множество сетей для заданной монеты."""
        try:
            networks = await redis_client.smembers(
                self.COIN_NETWORKS.format(coin=coin)
            )
            return networks
        except RedisError as e:
            logger.error('Error fetching networks for coin %s: %s',
                         coin, e, exc_info=True)

    async def get_coin_full_info(self, coin: str, network: str) -> Coin | None:
        """Получить полную информацию по монете на указанной сети."""
        coin_info = None
        try:
            coin_info = await redis_client.get(
                self.FULL_COIN_INFO_KEY.format(
                    coin=coin,
                    network=network
                )
            )
        except RedisError as e:
            logger.error('Error fetching info for coin %s on network %s: %s',
                         coin, network, e, exc_info=True)
        if coin_info:
            return Coin.model_validate_json(coin_info)

    async def get_rate(self, from_coin: str, from_network: str,
                       to_coin: str, to_network: str) -> schemas.RatesSchema | None:
        """Получить обменный курс между двумя монетами."""
        try:
            from_info = await self.get_coin_full_info(from_coin, from_network)
            to_info = await self.get_coin_full_info(to_coin, to_network)

            if not from_info or not to_info:
                logger.warning('Missing coin information for %s or %s.',
                               from_coin, to_coin)
                return None

            rate = await redis_client.get(
                self.RATE_KEY.format(
                    from_coin=from_info.code,
                    to_coin=to_info.code
                )
            )

            if not rate:
                logger.warning('Rate for coins %s -> %s is missing.',
                               from_coin, to_coin)
                return None

            return schemas.RatesSchema.model_validate_json(rate)
        except RedisError as e:
            logger.error('Error fetching exchange rate for %s -> %s: %s',
                         from_coin, to_coin, e, exc_info=True)


easybit_redis_client = EasybitRedisClient()