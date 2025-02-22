import asyncio
import json
import logging
from typing import Dict, Set
from redis.asyncio import StrictRedis
from src.config import config
from src.api.easybit.easybit_client import easybit_client

logger = logging.getLogger(__name__)

class LoadEasyBitDataToRedis:
    EXCHANGER = 'easybit'
    COINS_KEY = 'coins'
    COIN_NETWORKS = '{coin_name}:networks'
    SUPPORTED_RECEIVE_NETWORKS = 'supported_receive_networks'
    RATE_KEY = '{exchanger}:{type}:{from_coin}:{send_network}:to:{to_coin}:{receive_network}:info'

    def __init__(self):
        self.redis_client = StrictRedis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DATABASE,
            decode_responses=True
        )
        self.api_client = easybit_client

    async def load_currencies_and_networks(self) -> None:
        try:
            currency_list = await self.api_client.get_currency_list()
            if currency_list.success != 1:
                logger.error("Не удалось загрузить currency_list")
                return
            
            coins_set = set()
            coin_networks = {}
            supported_receive_networks: Dict[str, Set[str]] = {}
            
            for currency in currency_list.data:
                coins_set.add(currency.currency)
                if currency.currency not in coin_networks:
                    coin_networks[currency.currency] = set()
                for network_info in currency.network_list:
                    coin_networks[currency.currency].add(network_info.network)
                if currency.receive_status_all:
                    supported_receive_networks[currency.currency] = set()
                    for network_info in currency.network_list:
                        if network_info.receive_status:
                            supported_receive_networks[currency.currency].add(network_info.network)

            logger.debug(f"Загружено валют: {len(coins_set)}, поддерживаемых для получения: {len(supported_receive_networks)}")
            logger.debug(f"Поддерживаемые сети для получения: {supported_receive_networks}")

            await self.redis_client.delete(self.COINS_KEY)
            if coins_set:
                await self.redis_client.sadd(self.COINS_KEY, *coins_set)

            for coin, networks in coin_networks.items():
                key = self.COIN_NETWORKS.format(coin_name=coin)
                await self.redis_client.delete(key)
                if networks:
                    await self.redis_client.sadd(key, *networks)

            await self.redis_client.set(
                self.SUPPORTED_RECEIVE_NETWORKS,
                json.dumps({coin: list(networks) for coin, networks in supported_receive_networks.items()})
            )
            
            logger.info("Список валют и сетей успешно загружен")
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке списка валют: {str(e)}")
            raise

    async def load_rates(self) -> None:
        try:
            supported_networks_json = await self.redis_client.get(self.SUPPORTED_RECEIVE_NETWORKS)
            if not supported_networks_json:
                logger.error("Не удалось загрузить поддерживаемые сети из Redis")
                return
            supported_receive_networks: Dict[str, Set[str]] = {
                coin: set(networks) for coin, networks in json.loads(supported_networks_json).items()
            }
            logger.debug(f"Поддерживаемые сети для получения из Redis: {supported_receive_networks}")

            pair_list = await self.api_client.get_pair_list()
            if pair_list.success != 1:
                logger.error("API вернул неуспешный ответ для pair_list")
                return
            
            logger.debug(f"Получено пар из pair_list: {len(pair_list.data)}")
            processed_pairs = 0

            for pair_str in pair_list.data:
                try:
                    send, send_network, receive, receive_network = pair_str.split('_')
                    
                    if receive not in supported_receive_networks:
                        logger.debug(
                            f"Пропускаем пару {send}->{receive} ({send_network}->{receive_network}): "
                            "валюта получения не поддерживается"
                        )
                        continue
                    if receive_network not in supported_receive_networks[receive]:
                        logger.debug(
                            f"Пропускаем пару {send}->{receive} ({send_network}->{receive_network}): "
                            "сеть получения не поддерживается"
                        )
                        continue
                    
                    processed_pairs += 1
                    logger.debug(f"Обрабатываем пару: {send}->{receive} ({send_network}->{receive_network})")
                    
                    pair_info = await self.api_client.get_pair_info(
                        send=send,
                        receive=receive,
                        send_network=send_network,
                        receive_network=receive_network
                    )
                    if pair_info.success != 1:
                        logger.warning(
                            f"Пара {send}->{receive} ({send_network}->{receive_network}) "
                            f"недоступна в pairInfo: {pair_info.errorMessage or 'Неизвестная ошибка'}"
                        )
                        continue
                    
                    if pair_info.data and pair_info.data.minimumAmount and pair_info.data.maximumAmount:
                        min_amount = float(pair_info.data.minimumAmount)
                        max_amount = float(pair_info.data.maximumAmount)
                        amount = (min_amount + max_amount) / 2
                        logger.debug(f"Для пары {send}->{receive}: min={min_amount}, max={max_amount}, amount={amount}")
                    else:
                        logger.warning(
                            f"Недостаточно данных для пары {send}->{receive} "
                            f"({send_network}->{receive_network}): нет min/max amount"
                        )
                        continue
                    
                    rate_data = await self.api_client.get_rate(
                        send=send,
                        receive=receive,
                        amount=amount,
                        send_network=send_network,
                        receive_network=receive_network
                    )
                    if rate_data.success == 1:
                        key = self.RATE_KEY.format(
                            exchanger=self.EXCHANGER,
                            type='float',
                            from_coin=send,
                            send_network=send_network,
                            to_coin=receive,
                            receive_network=receive_network
                        )
                        value = json.dumps(rate_data.data.dict() if rate_data.data else {})
                        result = await self.redis_client.set(key, value)
                        if result:
                            logger.info(f"Курс для {send}->{receive} ({send_network}->{receive_network}) сохранен в Redis, ключ: {key}")
                        else:
                            logger.error(f"Не удалось сохранить курс для {send}->{receive} ({send_network}->{receive_network}) в Redis, ключ: {key}")
                    else:
                        logger.warning(
                            f"Пара {send}->{receive} ({send_network}->{receive_network}) "
                            f"недоступна в rate: {rate_data.errorMessage or 'Неизвестная ошибка'}"
                        )
                        continue
                        
                except Exception as e:
                    logger.warning(
                        f"Ошибка при загрузке курса для {send}->{receive} "
                        f"({send_network}->{receive_network}): {str(e)}"
                    )
                    continue
            
            logger.info(f"Курсы обмена успешно загружены, обработано пар: {processed_pairs}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке курсов обмена: {repr(e)}")
            raise

    async def run(self) -> None:
        while True:
            try:
                await self.load_currencies_and_networks()
                await self.load_rates()
                logger.info("Цикл обновления данных завершен")
            except Exception as e:
                logger.error(f"Ошибка в цикле обновления: {repr(e)}")
            await asyncio.sleep(10)

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.DEBUG)  # Установим DEBUG для полной отладки
#     loader = LoadEasyBitDataToRedis()
#     asyncio.run(loader.run())