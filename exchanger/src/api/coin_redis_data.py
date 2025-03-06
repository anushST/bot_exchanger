import logging

from redis.exceptions import RedisError

from src.api.schemas import Coin, RatesSchema
from src.enums import Exchangers, RateLoadedExchangers
from src.redis import redis_client

logger = logging.getLogger(__name__)


class CoinRedisDataClient:
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

    async def get_coin_full_info(self, exchanger: Exchangers, coin_name: str,
                                 network: str) -> Coin | None:
        """Retrieve full information for a coin on a specific network."""
        coin_info = None
        try:
            coin_info = await redis_client.get(
                self.FULL_COIN_INFO_KEY.format(
                    exchanger=exchanger.value,
                    coin_name=coin_name,
                    network=network
                )
            )
        except RedisError as e:
            logger.error('Error fetching coin info for %s on network %s: %s',
                         coin_name, network, e, exc_info=True)
        if coin_info:
            return Coin.model_validate_json(coin_info)

    async def get_coin_info(self, coin_name: str, network: str):
        exchangers = list(Exchangers)

        coin = Coin()
        for ex in exchangers:
            coin_info = await self.get_coin_full_info(
                ex, coin_name, network
            )
            if not coin_info:
                continue
            coin.coin = coin_info.coin if not coin.coin else coin.coin
            coin.code = coin_info.code if not coin.code else coin.coin
            coin.network = coin_info.network if not coin.network else coin.coin
            coin.receive = coin_info.receive if not coin.receive else coin.coin
            coin.send = coin_info.send if not coin.send else coin.coin
            coin.tag_name = coin_info.tag_name if not coin.tag_name else coin.coin # noqa
        return coin

    async def _get_rate(self, rate_type: str, exchanger: RateLoadedExchangers,
                        from_coin: str,
                        from_coin_network: str, to_coin: str,
                        to_coin_network: str) -> RatesSchema | None:
        """Retrieve exchange rate between two coins."""
        try:
            from_coin_info = await self.get_coin_full_info(
                exchanger, from_coin, from_coin_network)
            to_coin_info = await self.get_coin_full_info(
                exchanger, to_coin, to_coin_network)

            if not from_coin_info or not to_coin_info:
                return None

            rate = await redis_client.get(
                self.RATE_KEY.format(
                    exchanger=exchanger.value,
                    type=rate_type,
                    from_coin=from_coin_info.code,
                    to_coin=to_coin_info.code
                )
            )
            if not rate:
                return None
            rate = RatesSchema.model_validate_json(rate)
            if rate.validate_set_at():
                return rate
        except RedisError as e:
            logger.error('Error fetching exchange rate %s: %s',
                         rate_type, e, exc_info=True)

    async def get_fixed_rate(
            self, exchanger: RateLoadedExchangers, from_coin: str,
            from_coin_network: str,
            to_coin: str, to_coin_network: str) -> RatesSchema | None:
        """Retrieve fixed exchange rate between two coins."""
        return await self._get_rate('fixed', exchanger, from_coin,
                                    from_coin_network,
                                    to_coin, to_coin_network)

    async def get_float_rate(
            self, exchanger: RateLoadedExchangers, from_coin: str,
            from_coin_network: str,
            to_coin: str, to_coin_network: str) -> RatesSchema | None:
        """Retrieve floating exchange rate between two coins."""
        return await self._get_rate('float', exchanger, from_coin,
                                    from_coin_network,
                                    to_coin, to_coin_network)

    async def get_fixed_best_rate(self, from_coin: str, from_coin_network: str,
                                  to_coin: str, to_coin_network: str
                                  ) -> list[str, RatesSchema]:
        exchangers = list(RateLoadedExchangers)
        best_rate = 0
        rate_obj = None
        exchanger = None
        for ex in exchangers:
            rate_datas = await self.get_fixed_rate(
                ex, from_coin, from_coin_network, to_coin, to_coin_network
            )
            if rate_datas:
                rate = rate_datas.out_amount / rate_datas.in_amount
                if rate > best_rate:
                    best_rate = rate
                    rate_obj = rate_datas
                    exchanger = ex.value
        return [exchanger, rate_obj] if exchanger and rate_obj else []

    async def get_float_best_rate(self, from_coin: str, from_coin_network: str,
                                  to_coin: str, to_coin_network: str
                                  ) -> list[str, RatesSchema]:
        exchangers = list(RateLoadedExchangers)
        best_rate = 0
        rate_obj = None
        exchanger = None
        for ex in exchangers:
            rate_datas = await self.get_float_rate(
                ex, from_coin, from_coin_network, to_coin, to_coin_network
            )
            if rate_datas:
                rate = rate_datas.out_amount / rate_datas.in_amount
                if rate > best_rate:
                    best_rate = rate
                    rate_obj = rate_datas
                    exchanger = ex.value
        return [exchanger, rate_obj] if exchanger and rate_obj else []

    async def get_coin_in_usdt(self, coin, network) -> RatesSchema:
        networks_usdt = await coin_redis_data_client.get_networks('USDT')

        rate = None
        for net_usdt in networks_usdt:
            rate = await coin_redis_data_client.get_float_best_rate(
                coin, network, 'USDT', net_usdt)
            if rate:
                break
        return rate


coin_redis_data_client = CoinRedisDataClient()
