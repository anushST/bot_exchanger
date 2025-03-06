import logging
from redis.exceptions import RedisError as LibRedisError
from pydantic import ValidationError

from src.api.easybit import schemas
from src.api.schemas import Coin
from src.redis import redis_client
from src.api.exceptions import RedisError, RedisDataError

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
        except LibRedisError as e:
            logger.error('Error fetching coin list: %s', e, exc_info=True)
            raise RedisError(f'Ошибка при получении списка монет: {e}')

    async def get_networks(self, coin: str) -> set[str] | None:
        """Получить множество сетей для заданной монеты."""
        try:
            networks = await redis_client.smembers(
                self.COIN_NETWORKS.format(coin=coin)
            )
            return networks
        except LibRedisError as e:
            logger.error('Error fetching networks for coin %s: %s',
                         coin, e, exc_info=True)
            raise RedisError(f'Ошибка при получении сетей для монеты {coin}: {e}')

    async def get_coin_full_info(self, coin: str, network: str) -> Coin | None:
        """Получить полную информацию по монете на указанной сети."""
        try:
            coin_info = await redis_client.get(
                self.FULL_COIN_INFO_KEY.format(
                    coin=coin,
                    network=network
                )
            )
            if not coin_info:
                return None
                
            try:
                return Coin.model_validate_json(coin_info)
            except ValidationError as e:
                logger.error('Error validating coin data for %s on network %s: %s',
                            coin, network, e, exc_info=True)
                raise RedisDataError(f'Ошибка валидации данных монеты {coin} в сети {network}: {e}')
                
        except LibRedisError as e:
            logger.error('Error fetching info for coin %s on network %s: %s',
                         coin, network, e, exc_info=True)
            raise RedisError(f'Ошибка при получении информации о монете {coin} в сети {network}: {e}')

    async def get_rate(self, from_coin: str, from_network: str,
                       to_coin: str, to_network: str) -> schemas.RateResponse | None:
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

            try:
                return schemas.RateResponse.model_validate_json(rate)
            except ValidationError as e:
                logger.error('Error validating rate data for %s -> %s: %s',
                            from_coin, to_coin, e, exc_info=True)
                raise RedisDataError(f'Ошибка валидации данных курса обмена {from_coin} -> {to_coin}: {e}')
                
        except LibRedisError as e:
            logger.error('Error fetching exchange rate for %s -> %s: %s',
                         from_coin, to_coin, e, exc_info=True)
            raise RedisError(f'Ошибка при получении курса обмена {from_coin} -> {to_coin}: {e}')


easybit_redis_client = EasybitRedisClient()