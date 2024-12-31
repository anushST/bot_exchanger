import time
import json
import hmac
import hashlib
import asyncio
import aiohttp
from typing import Optional, List, Any
from pydantic import BaseModel, Field


#
# Pydantic модели
#

class JsonRPCRequest(BaseModel):
    """
    Модель для формирования JSON-RPC запроса к Changelly.
    """
    jsonrpc: str = "2.0"
    id: int = Field(default_factory=lambda: int(time.time()))
    method: str
    params: dict = Field(default_factory=dict)


class ErrorModel(BaseModel):
    """
    Модель для описания объекта ошибки в ответе Changelly (если она есть).
    """
    code: Optional[int] = None
    message: Optional[str] = None


class JsonRPCResponse(BaseModel):
    """
    Базовая структура JSON-RPC ответа.
    """
    jsonrpc: str
    id: int
    result: Optional[Any] = None
    error: Optional[ErrorModel] = None


#
# Модели входных параметров (RequestParams)
#

class GetMinAmountParams(BaseModel):
    from_currency: str = Field(..., alias="from")
    to_currency: str = Field(..., alias="to")


class GetExchangeAmountParams(GetMinAmountParams):
    amount: float


class CreateTransactionParams(GetExchangeAmountParams):
    address: str
    refund_address: str = Field(..., alias="refundAddress")
    # При необходимости: memo, tag, paymentId и т.д.


class GetTransactionsParams(BaseModel):
currency: Optional[str] = None
limit: int = 10


#
# Модели ответа (ResponseModels)
#

class TransactionData(BaseModel):
    """
    Упрощенная модель данных о транзакции (пример).
    """
    id: str
    payinAddress: Optional[str]
    payoutAddress: Optional[str]
    fromCurrency: Optional[str]
    toCurrency: Optional[str]
    amount: Optional[float]
    status: Optional[str]
    # Дополнительные поля при необходимости


class CurrenciesResponse(BaseModel):
    """
    Пример ответа для getCurrencies - массив строк (e.g. ["btc","eth","usdt",...]).
    """
    __root__: List[str]


class TransactionsListResponse(BaseModel):
    """
    Пример ответа для getTransactions - массив транзакций.
    """
    __root__: List[TransactionData]


#
# Асинхронный клиент с использованием aiohttp
#

class ChangellyAsyncClient:
    """
    Пример асинхронного клиента для Changelly Merchant API (v2) с Pydantic.
    Документация: https://docs.changelly.com/changelly-merchant-api/
    По умолчанию используется URL: https://apiv4.changelly.com
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://apiv4.changelly.com"):
        """
        :param api_key:    Ваш API Key из личного кабинета Changelly
        :param api_secret: Ваш Secret Key (HMAC SHA-512)
        :param base_url:   Базовый URL для запросов к Changelly (по умолчанию prod URL)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url

    def _generate_signature(self, body: dict) -> str:
        """
        Генерация подписи (HMAC SHA-512) для тела запроса.
        :param body: dict, который далее будет преобразован в JSON для запроса.
        :return: Hex-строка с HMAC SHA-512 подписью.
        """
        # Преобразуем тело (dict) в JSON-строку (без лишних пробелов)
        json_data = json.dumps(body, separators=(',', ':'))
        # Создаем HMAC SHA-512
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            json_data.encode("utf-8"),
            hashlib.sha512
        ).hexdigest()
        return signature

    async def _request(self, method: str, params: dict = None) -> Any:
        """
        Универсальная функция для формирования и отправки запроса к Changelly (асинхронно).
        :param method: Название метода Changelly (например, 'getCurrencies').
        :param params: Параметры, передаваемые в метод (dict).
        :return: результат (result) из ответа Changelly (если нет ошибки).
        :raises Exception: при возникновении ошибок (HTTP или JSON-RPC error).
        """
        if params is None:
            params = {}

        # Формируем тело запроса через Pydantic-модель
        rpc_request = JsonRPCRequest(method=method, params=params)

        # Генерируем подпись
        signature = self._generate_signature(rpc_request.model_dump(by_alias=True))

        # Заголовки
        headers = {
            "Content-Type": "application/json",
            "TNT-API-Key": self.api_key,   # согласно Changelly v2
            "TNT-API-Sign": signature
        }

        # Выполняем асинхронный POST-запрос
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                headers=headers,
                data=rpc_request.model_dump_json(by_alias=True, separators=(',', ':'))
            ) as response:

                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Changelly API error (HTTP {response.status}): {text}")

                # Читаем и парсим JSON
                data = await response.json()

        # Валидируем базовую структуру JSON-RPC ответа
        try:
            rpc_response = JsonRPCResponse(**data)
        except Exception as exc:
            raise Exception(f"Invalid JSON-RPC response format: {exc}")

        # Проверяем, не вернулась ли ошибка со стороны Changelly
        if rpc_response.error:
            raise Exception(
                f"Changelly API returned error: {rpc_response.error.message} "
                f"(code: {rpc_response.error.code})"
            )

        return rpc_response.result

    # --- Методы Changelly Merchant API (v2) ---

    async def get_currencies(self) -> List[str]:
        """
        Получение списка поддерживаемых валют (пример).
        :return: список строк (e.g. ["btc","eth","usdt",...])
        """
        result = await self._request(method="getCurrencies")
        # Валидируем ответ как массив строк
        validated = CurrenciesResponse.model_validate(result)
        return validated.__root__

    async def get_min_amount(self, from_currency: str, to_currency: str) -> float:
        """
        Получение минимально допустимого объема обмена.
        :param from_currency: исходная валюта (e.g. 'btc')
        :param to_currency:   целевая валюта (e.g. 'eth')
        :return: float
        """
        params_model = GetMinAmountParams(
            from_currency=from_currency,
            to_currency=to_currency
        )
        result = await self._request(
            method="getMinAmount",
            params=params_model.dict(by_alias=True)
        )
        # Возвращаем как float
        return float(result)

    async def get_exchange_amount(self, from_currency: str, to_currency: str, amount: float) -> float:
        """
        Получение количества to_currency, которое будет выдано за amount from_currency.
        """
        params_model = GetExchangeAmountParams(
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount
        )
        result = await self._request(
            method="getExchangeAmount",
            params=params_model.dict(by_alias=True)
        )
        return float(result)

    async def create_transaction(
        self,
        from_currency: str,
        to_currency: str,
        amount: float,
        address: str,
        refund_address: str
    ) -> TransactionData:
        """
        Создание транзакции на обмен.
        :param from_currency: исходная валюта (e.g. 'btc')
        :param to_currency:   целевая валюта (e.g. 'eth')
        :param amount:        количество исходной валюты
        :param address:       кошелёк получателя
        :param refund_address: кошелёк для возврата
        """
        params_model = CreateTransactionParams(
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
            address=address,
            refund_address=refund_address
        )
        result = await self._request(
            method="createTransaction",
            params=params_model.model_dump(by_alias=True)
        )
        # Предположим, что результат содержит необходимые поля для TransactionData
        return TransactionData(**result)

    async def get_transactions(self, currency: Optional[str] = None, limit: int = 10) -> List[TransactionData]:
        """
        Получение списка транзакций, созданных через ваш аккаунт.
        """
        params_model = GetTransactionsParams(currency=currency, limit=limit)
        result = await self._request(
            method="getTransactions",
            params=params_model.model_dump(exclude_none=True)
        )
        validated = TransactionsListResponse.model_validate(result)
        return validated.__root__

async def main():
    # Пример (значения ниже не являются реальными ключами)
    API_KEY = "YOUR_CHANGELLY_API_KEY"
    API_SECRET = "YOUR_CHANGELLY_API_SECRET"

    changelly = ChangellyAsyncClient(api_key=API_KEY, api_secret=API_SECRET)

    try:
        # 1. Получение списка поддерживаемых валют
        currencies = await changelly.get_currencies()
        print("Currencies:", currencies)

        # 2. Минимальный объём обмена (BTC -> ETH)
        min_amount = await changelly.get_min_amount("btc", "eth")
        print("Min amount BTC->ETH:", min_amount)

        # 3. Расчёт конкретного количества ETH при обмене 0.01 BTC
        exchange_amount = await changelly.get_exchange_amount("btc", "eth", 0.01)
        print("Exchange amount for 0.01 BTC -> ETH:", exchange_amount)

        # 4. Создание транзакции (раскомментируйте и подставьте реальные адреса для теста)
        # new_tx = await changelly.create_transaction(
        #     from_currency="btc",
        #     to_currency="eth",
        #     amount=0.01,
        #     address="YOUR_ETH_ADDRESS",
        #     refund_address="YOUR_BTC_REFUND_ADDRESS"
        # )
        # print("New transaction:", new_tx.dict())

        # 5. Получение списка транзакций (фильтр по ETH, 5 штук):
        # tx_list = await changelly.get_transactions(currency="eth", limit=5)
        # for tx in tx_list:
        #     print(tx.dict())

    except Exception as e:
        print("Error:", str(e))


if __name__ == "__main__":
    asyncio.run(main())
