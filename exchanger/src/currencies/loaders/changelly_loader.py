import logging

from src.api.schemas import Coin
from src.api.changelly import changelly_client
from src.redis import redis_client

logger = logging.getLogger(__name__)


class LoadChangellyDataToRedis:
    EXCHANGER = 'changelly'
    COINS_KEY = 'coins'
    COIN_NETWORKS = '{coin_name}:networks'
    FULL_COIN_INFO_KEY = '{exchanger}:{coin_name}:{network}:info'
    RATE_KEY = '{exchanger}:{type}:{from_coin}:to:{to_coin}:info'

    async def load_currencies_and_networks(self) -> None:
        coins_full_info = await changelly_client.get_currencies_full()

        for coin in coins_full_info:
            await redis_client.sadd(self.COINS_KEY, coin.coin.upper())
            await redis_client.sadd(
                self.COIN_NETWORKS.format(coin_name=coin.coin.upper()),
                coin.network.upper()
            )
            await redis_client.set(
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
