import os
import asyncio
import logging
from typing import Any, Dict, Optional
import aiohttp
from aiohttp import ClientError
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из .env
from . import constants as const
from .schemas.currencies_list import CurrencyListResponse
from .schemas.order import CreateOrderRequest, OrderResponse, OrderStatusResponse
from .schemas.rates import PairListResponse, PairInfoResponse

logger = logging.getLogger(__name__)


class EasyBitClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("EASYBIT_API_KEY")
        if not self.api_key:
            raise ValueError("Не задан API ключ. Проверьте переменную окружения EASYBIT_API_KEY.")
        self.base_url = "https://api.easybit.com"
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {"API-KEY": self.api_key}
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for attempt in range(const.MAX_RETRIES):
                try:
                    async with session.request(
                        method=method, url=url, headers=headers, params=params, json=data
                    ) as response:
                        response.raise_for_status()
                        return await response.json()
                except ClientError as e:
                    logger.warning(f"Request error: {e}, attempt {attempt + 1}")
                    if attempt == const.MAX_RETRIES - 1:
                        raise
                    await asyncio.sleep(const.RETRY_DELAY * (attempt + 1))

    async def account(self) -> Dict[str, Any]:
        """
        Получить данные аккаунта по API.
        Возвращает словарь с данными аккаунта.
        """
        return await self._request("GET", "/account")

    async def get_currency_list(self) -> CurrencyListResponse:
        response = await self._request("GET", "/currencyList")
        return CurrencyListResponse(**response)

    async def get_pair_list(self) -> PairListResponse:
        response = await self._request("GET", "/pairList")
        return PairListResponse(**response)

    async def get_pair_info(
        self,
        send: str,
        receive: str,
        send_network: Optional[str] = None,
        receive_network: Optional[str] = None,
    ) -> PairInfoResponse:
        """
        Получить информацию о паре обмена.
        :param send: Валюта для отправки.
        :param receive: Валюта для получения.
        :param send_network: Сеть для отправки (опционально).
        :param receive_network: Сеть для получения (опционально).
        """
        params = {
            "send": send,
            "receive": receive,
        }
        if send_network:
            params["sendNetwork"] = send_network
        if receive_network:
            params["receiveNetwork"] = receive_network

        response = await self._request("GET", "/pairInfo", params=params)
        return PairInfoResponse(**response)

    async def get_rate(
        self,
        send: str,
        receive: str,
        amount: float,
        send_network: Optional[str] = None,
        receive_network: Optional[str] = None,
        amount_type: Optional[str] = None,
        extra_fee_override: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Получить обменный курс для указанной пары.
        :param send: Валюта для отправки.
        :param receive: Валюта для получения.
        :param amount: Сумма для отправки.
        :param send_network: Сеть для отправки (опционально).
        :param receive_network: Сеть для получения (опционально).
        :param amount_type: Тип суммы ("send" или "receive") (опционально).
        :param extra_fee_override: Переопределение дополнительной комиссии (опционально).
        """
        params = {
            "send": send,
            "receive": receive,
            "amount": amount,
        }
        if send_network:
            params["sendNetwork"] = send_network
        if receive_network:
            params["receiveNetwork"] = receive_network
        if amount_type:
            params["amountType"] = amount_type
        if extra_fee_override is not None:
            params["extraFeeOverride"] = extra_fee_override

        return await self._request("GET", "/rate", params=params)

    async def create_order(self, order_data: CreateOrderRequest) -> OrderResponse:
        response = await self._request("POST", "/order", data=order_data.model_dump())
        return OrderResponse(**response)

    async def get_order_status(self, order_id: str) -> OrderStatusResponse:
        params = {"order_id": order_id}
        response = await self._request("GET", "/orderStatus", params=params)
        return OrderStatusResponse(**response)

    async def get_orders(self) -> Dict[str, Any]:
        """
        Получить информацию обо всех заказах.
        Функция возвращает сырой JSON, для которого нужно будет создать соответствующую схему.
        """
        return await self._request("GET", "/orders")


# Создаем экземпляр клиента для использования в других модулях
easybit_client = EasyBitClient()