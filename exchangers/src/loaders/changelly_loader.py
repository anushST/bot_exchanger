import logging

from redis.asyncio import StrictRedis

from src.api.schemas import Coin, RatesSchema
from src.config import config
from src.api.changelly import changelly_client
from src.api.changelly import schemas

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
                Coin(
                    code=coin.ticker,
                    coin=coin.coin,
                    network=coin.network,
                    receive=coin.enabled_from,
                    send=coin.enabled_to,
                    tag_name=coin.extra_id_name
                ).model_dump_json(by_alias=True)
            )

    async def _load_rates(self, rates: list, type: str):
        for rate in rates:
            await self.redis_client.set(
                self.RATE_KEY.format(
                    exchanger=self.EXCHANGER,
                    type=type,
                    from_coin=rate.from_coin,
                    to_coin=rate.to_coin
                ),
                RatesSchema(
                    from_coin=rate.from_,
                    to=rate.to,
                    in_amount=rate.amount_from,
                    out_amount=rate.amount_to,
                    to_network_fee=rate.network_fee,
                    min_from_amount=rate.min_from,
                    max_from_amount=rate.max_from,
                    min_to_amount=rate.min_to,
                    max_to_amount=rate.max_to
                ).model_dump_json(by_alias=True)
            )

    async def load_fixed_rates(self):
        fixed_rates = await changelly_client.get_fixed_estimates()
        await self._load_rates(fixed_rates, 'fixed')

    async def load_float_rates(self):
        float_rates = await changelly_client.get_float_estimates()
        await self._load_rates(float_rates, 'float')
