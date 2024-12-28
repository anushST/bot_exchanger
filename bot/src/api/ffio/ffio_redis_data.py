import logging

from redis.exceptions import RedisError

from src.api.ffio import schemas
from src.redis import redis_client

logger = logging.getLogger(__name__)


class FFIORedisClient:
    EXCHANGER = 'ffio'
    COINS_KEY = 'coins'
    COIN_NETWORKS = '{coin_name}:networks'
    FULL_COIN_INFO_KEY = '{exchanger}:{coin_name}:{network}:info'
    RATE_KEY = '{exchanger}:{type}:{from_coin}:to:{to_coin}:info'

    async def get_coins(self) -> set[str] | None:
        """Retrieve the set of available coins."""
        try:
            return await redis_client.smembers(self.COINS_KEY)
        except RedisError as e:
            logger.error('Error fetching coin list: %s', e, exc_info=True)

    async def get_networks(self, coin_name: str) -> set[str] | None:
        """Retrieve the set of networks for a given coin."""
        try:
            networks = await redis_client.smembers(
                self.COIN_NETWORKS.format(coin_name=coin_name))
            return networks
        except RedisError as e:
            logger.error('Error fetching networks for coin %s: %s',
                         coin_name, e, exc_info=True)

    async def get_coin_full_info(self, coin_name: str,
                                 network: str) -> schemas.Currency | None:
        """Retrieve full information for a coin on a specific network."""
        coin_info = None
        try:
            coin_info = await redis_client.get(
                self.FULL_COIN_INFO_KEY.format(
                    exchanger=self.EXCHANGER,
                    coin_name=coin_name,
                    network=network
                )
            )
        except RedisError as e:
            logger.error('Error fetching coin info for %s on network %s: %s',
                         coin_name, network, e, exc_info=True)
        return schemas.Currency.model_validate_json(coin_info)

    async def _get_rate(self, rate_type: str, from_coin: str,
                        from_coin_network: str, to_coin: str,
                        to_coin_network: str) -> schemas.RatesSchema | None:
        """Retrieve exchange rate between two coins."""
        try:
            from_coin_info = await self.get_coin_full_info(
                from_coin, from_coin_network)
            to_coin_info = await self.get_coin_full_info(
                to_coin, to_coin_network)

            if not from_coin_info or not to_coin_info:
                logger.warning('Missing coin information for %s or %s.',
                               from_coin, to_coin)
                return None

            rate = await redis_client.get(
                self.RATE_KEY.format(
                    exchanger=self.EXCHANGER,
                    type=rate_type,
                    from_coin=from_coin_info.code,
                    to_coin=to_coin_info.code
                )
            )
            if not rate:
                logger.warning('Rate %s for coins %s -> %s is missing.',
                               rate_type, from_coin, to_coin)
                return None
            return schemas.RatesSchema.model_validate_json(rate)
        except RedisError as e:
            logger.error('Error fetching exchange rate %s: %s',
                         rate_type, e, exc_info=True)

    async def get_fixed_rate(
            self, from_coin: str, from_coin_network: str,
            to_coin: str, to_coin_network: str) -> schemas.RatesSchema | None:
        """Retrieve fixed exchange rate between two coins."""
        return await self._get_rate('fixed', from_coin, from_coin_network,
                                    to_coin, to_coin_network)

    async def get_float_rate(
            self, from_coin: str, from_coin_network: str,
            to_coin: str, to_coin_network: str) -> schemas.RatesSchema | None:
        """Retrieve floating exchange rate between two coins."""
        return await self._get_rate('float', from_coin, from_coin_network,
                                    to_coin, to_coin_network)


ffio_redis_client = FFIORedisClient()
