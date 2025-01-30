import logging

from redis.asyncio import StrictRedis

from src.config import config
from src.api.changelly import changelly_client

logger = logging.getLogger(__name__)


class LoadChangellyDataToRedis:
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

    async def load_currencies_and_networks(self) -> None:
        coins = await changelly_client.get_currencies_list()
        coins_full_info = await changelly_client.get_currencies_full()
        print(await changelly_client.get_fixed_estimates())

        for coin in coins:
            await self.redis_client.sadd(self.COINS_KEY, coin.upper())

        for coin in coins_full_info:
            await self.redis_client.sadd(
                self.COIN_NETWORKS.format(coin_name=coin.coin.upper()),
                coin.network.upper()
            )
            await self.redis_client.set(
                self.FULL_COIN_INFO_KEY.format(
                    exchanger=self.EXCHANGER,
                    coin_name=coin.coin.upper(),
                    network=coin.network.upper()
                ),
                coin.model_dump_json()
            )

        logger.info('Currencies and networks loaded successfully')

    async def _load_rates(self, rates, type: str):
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
        fixed_rates = await changelly_client.get_fixed_rates()
        await self._load_rates(fixed_rates, 'fixed')
        logger.info('Fixed rates loaded successfully')

    async def load_float_rates(self):
        float_rates = await changelly_client.get_float_rates()
        await self._load_rates(float_rates, 'float')
        logger.info('Float rates loaded successully')
