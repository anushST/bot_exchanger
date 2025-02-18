import logging
from collections import defaultdict
import asyncio
import json

from redis.asyncio import StrictRedis

from src.config import config
from src.api.schemas import Coin
from src.api.easybit.easybit_client import easybit_client

logger = logging.getLogger(__name__)

class LoadEasyBitDataToRedis:
    EXCHANGER = 'easybit'
    COINS_KEY = '{exchanger}:coins'
    COIN_NETWORKS = '{exchanger}:{coin_name}:networks'
    FULL_COIN_INFO_KEY = '{exchanger}:{coin_name}:{network}:info'
    RATE_KEY = '{exchanger}:rate:{from_coin}:to:{to_coin}:info'

    def __init__(self):
        self.redis_client = StrictRedis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DATABASE,
            decode_responses=True
        )
        self.api_client = easybit_client

    async def load_currencies_and_networks(self) -> None:
        """
        Загружает данные о валютах и сетях.
        - Сохраняет подробную информацию о каждой валюте и сети в Redis.
        - Добавляет названия валют в множество COINS_KEY.
        - Сохраняет наборы сетей для каждой валюты.
        """
        currency_response = await self.api_client.get_currency_list()
        if currency_response.success != 1:
            logger.warning("Не удалось получить список валют.")
            return

        currencies = currency_response.data
        coins_set = set()
        coin_networks = defaultdict(set)

        for currency in currencies:
            coins_set.add(currency.currency)
            for network in currency.network_list:
                coin_networks[currency.currency].add(network.network)
                coin_info = {
                    "code": currency.currency,
                    "coin": currency.currency,
                    "network": network.network,
                    "receive": network.receive_status,
                    "send": network.send_status,
                    "tag_name": network.tag_name
                }
                key = self.FULL_COIN_INFO_KEY.format(
                    exchanger=self.EXCHANGER,
                    coin_name=currency.currency,
                    network=network.network
                )
                await self.redis_client.set(key, json.dumps(coin_info))

        # Сохраняем список валют
        coins_key = self.COINS_KEY.format(exchanger=self.EXCHANGER)
        await self.redis_client.delete(coins_key)
        await self.redis_client.sadd(coins_key, *list(coins_set))

        # Сохраняем сети для каждой валюты
        for coin, networks in coin_networks.items():
            coin_network_key = self.COIN_NETWORKS.format(
                exchanger=self.EXCHANGER,
                coin_name=coin
            )
            await self.redis_client.delete(coin_network_key)
            await self.redis_client.sadd(coin_network_key, *list(networks))

    async def load_supported_pairs(self):
        """
        Получает список поддерживаемых пар валют из API.
        """
        pair_list_response = await self.api_client.get_pair_list()
        if pair_list_response.success != 1:
            logger.warning("Не удалось получить список пар.")
            return []

        supported_pairs = pair_list_response.data
        logger.debug(f"Поддерживаемые пары: {supported_pairs}")
        return supported_pairs

    async def load_rates(self):
        """
        Загружает курсы валют для всех поддерживаемых пар.
        Сохраняет данные о курсах в Redis.
        """
        supported_pairs = await self.load_supported_pairs()

        for pair_id in supported_pairs:
            try:
                logger.debug(f"Обработка пары: {pair_id}")

                # Разбиваем pair_id
                parts = pair_id.split("_")
                if len(parts) < 2:
                    logger.warning(f"Неверный формат пары: {pair_id}.")
                    continue

                from_coin = parts[0]
                to_coin = parts[1]
                send_network = parts[2] if len(parts) > 2 else None
                receive_network = parts[3] if len(parts) > 3 else None

                # Задаем фиксированную сумму для отправки
                amount = 1.0

                # Логируем параметры запроса
                logger.debug(
                    f"Запрос курса для пары {pair_id}: "
                    f"send={from_coin}, receive={to_coin}, amount={amount}, "
                    f"send_network={send_network}, receive_network={receive_network}"
                )

                # Запрашиваем курс
                rate_response = await self.api_client.get_rate(
                    send=from_coin,
                    receive=to_coin,
                    amount=amount,
                    send_network=send_network,
                    receive_network=receive_network
                )

                logger.debug(f"Ответ от API для пары {pair_id}: {rate_response}")

                if isinstance(rate_response, dict) and rate_response.get("success") != 1:
                    logger.warning(f"Не удалось получить курс для пары {pair_id}.")
                    continue

                # Обрабатываем данные курса
                rate_data = rate_response.get("data")
                key = self.RATE_KEY.format(
                    exchanger=self.EXCHANGER,
                    from_coin=from_coin,
                    to_coin=to_coin
                )
                await self.redis_client.set(key, json.dumps(rate_data))
                logger.debug(f"Курс сохранен под ключом: {key}")

            except Exception as e:
                logger.error(f"Ошибка при загрузке курса для пары {pair_id}: {e}")

    async def load_all(self):
        """
        Параллельно запускает задачи загрузки данных.
        """
        try:
            await asyncio.gather(
                self.load_currencies_and_networks(),
                self.load_rates()
            )
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {e}")