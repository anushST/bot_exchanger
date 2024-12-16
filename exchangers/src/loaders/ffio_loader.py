import logging
from collections import defaultdict

from redis.asyncio import StrictRedis

from src.config import config
from src.api.ffio import schemas
from src.api.ffio.ffio_client import FFIOClient

logger = logging.getLogger(__name__)


class LoadFFIODataToRedis:
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
        self.api_client = FFIOClient(
            key=config.FFIO_APIKEY,
            secret=config.FFIO_SECRET
        )

    async def _remove_currencies_ununiqueness(
            self, coins) -> list[schemas.Currency]:
        grouped_coins = defaultdict(list)

        for coin in coins:
            key = (coin.coin, coin.network)
            grouped_coins[key].append(coin)

        filtered_coins = []

        for key, group in grouped_coins.items():
            if len(group) == 1:
                filtered_coins.append(group[0])
            else:
                codes = ', '.join(coin.code for coin in group)
                logger.info(f'Removed pair {key[0]}/{key[1]}, values: {codes}')

        return filtered_coins

    async def load_currencies_and_networks(self) -> None:
        coins = await self.api_client.ccies()
        coins = await self._remove_currencies_ununiqueness(coins)

        coins_set = set()
        coin_networks = defaultdict(set)

        for coin in coins:
            # await self.redis_client.sadd(self.COINS_KEY, coin.coin)
            # await self.redis_client.sadd(
            #     self.COIN_NETWORKS.format(coin_name=coin.coin),
            #     coin.network
            # )
            coins_set.add(coin.coin)
            coin_networks[coin.coin].add(coin.network)
            await self.redis_client.set(
                self.FULL_COIN_INFO_KEY.format(
                    exchanger=self.EXCHANGER,
                    coin_name=coin.coin,
                    network=coin.network
                ),
                coin.model_dump_json()
            )

        await self.redis_client.delete(self.COINS_KEY)
        await self.redis_client.sadd(self.COINS_KEY, *coins_set)

        for coin, networks in coin_networks.items():
            await self.redis_client.delete(
                self.COIN_NETWORKS.format(coin_name=coin)
            )
            await self.redis_client.sadd(
                self.COIN_NETWORKS.format(coin_name=coin),
                *networks
            )

        logger.info('Currencies and networks loaded successfully')

    async def _load_rates(self, rates: list[schemas.RatesSchema], type: str):
        for rate in rates:
            await self.redis_client.set(
                self.RATE_KEY.format(
                    exchanger=self.EXCHANGER,
                    type=type,
                    from_coin=rate.from_coin,
                    to_coin=rate.to_coin
                ),
                rate.model_dump_json(by_alias=True)
            )

    async def load_fixed_rates(self):
        fixed_rates = await self.api_client.get_fixed_rates()
        await self._load_rates(fixed_rates, 'fixed')
        logger.info('Fixed rates loaded successfully')

    async def load_float_rates(self):
        float_rates = await self.api_client.get_float_rates()
        await self._load_rates(float_rates, 'float')
        logger.info('Float rates loaded successully')
