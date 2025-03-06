import logging

from src.api.easybit.easybit_client import easybit_client
from src.exceptions import ClientError
from src.redis import redis_client
from src.api.schemas import Coin

logger = logging.getLogger(__name__)


class LoadEasyBitDataToRedis:
    EXCHANGER = 'easybit'
    COINS_KEY = 'coins'
    COIN_NETWORKS = '{coin_name}:networks'
    FULL_COIN_INFO_KEY = '{exchanger}:{coin_name}:{network}:info'
    RATE_KEY = '{exchanger}:{type}:{from_coin}:{send_network}:to:{to_coin}:{receive_network}:info' # noqa

    async def load_currencies_and_networks(self) -> None:
        try:
            response = await easybit_client.get_currency_list()

            if hasattr(response, 'data'):
                currencies = response.data
            else:
                currencies = response

            for currency in currencies:
                if isinstance(currency, tuple):
                    logger.debug(f"Currency is a tuple: {currency}")
                    continue

                coin_name = currency.currency.upper()
                await redis_client.sadd(self.COINS_KEY, coin_name)

                for network_info in currency.network_list:
                    network = network_info.network.upper()
                    await redis_client.sadd(
                        self.COIN_NETWORKS.format(coin_name=coin_name),
                        network
                    )

                    await redis_client.set(
                        self.FULL_COIN_INFO_KEY.format(
                            exchanger=self.EXCHANGER,
                            coin_name=coin_name,
                            network=network
                        ),
                        Coin(
                            code=currency.currency,
                            coin=currency.currency,
                            network=network_info.network,
                            receive=network_info.receive_status,
                            send=network_info.send_status,
                            tag_name=network_info.tag_name if hasattr(network_info, 'tag_name') else None # noqa
                        ).model_dump_json(by_alias=True)
                    )

            logger.info("Currency and network list successfully loaded")

        except ClientError as e:
            logger.error(f"Error loading currency list: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error loading currency list: {e}",
                         exc_info=True)
