import asyncio
import base64
import binascii
import hashlib
import hmac
import json
import logging
from decimal import Decimal
from typing import Optional
import time
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from requests import post, Response

import aiohttp
import xmltodict
from aiohttp import ClientError, ClientTimeout
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class JsonRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int = Field(default_factory=lambda: int(time.time()))
    method: str
    params: dict = Field(default_factory=dict)


class ErrorModel(BaseModel):
    code: Optional[int] = None
    message: Optional[str] = None


class JsonRPCResponse(BaseModel):
    jsonrpc: str
    id: int
    result: Optional[Any] = None
    error: Optional[ErrorModel] = None


class GetMinAmountParams(BaseModel):
    from_currency: str = Field(..., alias="from")
    to_currency: str = Field(..., alias="to")


class GetExchangeAmountParams(GetMinAmountParams):
    amount: float


class CreateTransactionParams(GetExchangeAmountParams):
    address: str
    refund_address: str = Field(..., alias="refundAddress")


class GetTransactionsParams(BaseModel):
    currency: Optional[str] = None
    limit: int = 10


class ChangellyClient:

    def __init__(self, private_key: str, x_api_key: str,
                 timeout: int = 10) -> None:
        self.private_key = private_key
        self.x_api_key = x_api_key
        self.timeout = ClientTimeout(total=timeout)

    def _sign_request(self, body: dict) -> bytes:
        decoded_private_key = binascii.unhexlify(self.private_key)
        private_key = RSA.import_key(decoded_private_key)
        message = json.dumps(body).encode('utf-8')
        h = SHA256.new(message)
        signature = pkcs1_15.new(private_key).sign(h)
        return base64.b64encode(signature).decode("utf-8")

    def _get_headers(self, body: dict) -> dict:
        signature = self._sign_request(body)
        return {
            'Content-Type': 'application/json',
            'X-Api-Key': self.x_api_key,
            'X-Api-Signature': signature,
        }

    async def _request(self, method: str, params: dict = None) -> Any:
        if params is None:
            params = {}

        rpc_request = JsonRPCRequest(method=method, params=params)

        headers = self._get_headers(rpc_request.model_dump())

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                'https://api.changelly.com/v2/',
                headers=headers,
                json=rpc_request.model_dump()
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    print(text)
                    raise Exception(f"Changelly API error (HTTP {response.status}): {text}")

                data = await response.json()

        try:
            print(data)
        except Exception as exc:
            raise Exception(f"Invalid JSON-RPC response format: {exc}")

        # if rpc_response.error:
        #     raise Exception(
        #         f"Changelly API returned error: {rpc_response.error.message} "
        #         f"(code: {rpc_response.error.code})"
        #     )

        # return rpc_response.result

    async def get_currencies(self) -> List[str]:
        result = await self._request(method="getCurrencies")
        return result

    async def get_min_amount(self, from_currency: str, to_currency: str) -> float:
        params_model = GetMinAmountParams(
            from_currency=from_currency,
            to_currency=to_currency
        )
        result = await self._request(
            method="getMinAmount",
            params=params_model.model_dump(by_alias=True)
        )
        return result

    async def get_exchange_amount(self, from_currency: str, to_currency: str, amount: float) -> float:
        params_model = GetExchangeAmountParams(
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount
        )
        result = await self._request(
            method="getExchangeAmount",
            params=params_model.model_dump(by_alias=True)
        )
        return result

    async def create_transaction(
        self,
        from_currency: str,
        to_currency: str,
        amount: float,
        address: str,
        refund_address: str
    ):
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
        return result

    async def get_transactions(self, currency: Optional[str] = None, limit: int = 10):
        params_model = GetTransactionsParams(currency=currency, limit=limit)
        result = await self._request(
            method="getTransactions",
            params=params_model.model_dump(exclude_none=True)
        )
        return result
    
    async def get_pairs_params(self, currency_from: str, currency_to: str):
        return await self._request('getPairsParams', params=[{'from': currency_from, 'to': currency_to}])

async def main():
    changelly_client = ChangellyClient(
        '308204bc020100300d06092a864886f70d0101010500048204a6308204a20201000282010100bdde7cb36e92b8d10d9ef3f036746988b1b384e6ac05df9173316de50519275410fad574eae2690388b41b2f7e018cd3815f1d99e4c2f7f56171c20e78580254fe43f4d2d1cee2d52272e23054eb829b7f5a749a775a784cd48983e22dddbf70d71bc6914621e3c56b2d682585ae368044f3c17ad5b901db4bd7e8b18aea696b36e3ebcc2424c02f6ba72bc1f304ee0dee67c3da31a7544f2a2d413babfe4c613ef604358ee64a7e748b1bc9636c4668693b89d03a1d7531ecf991572112e37a4f8f19b3e4829f3789d9423f0fa35d865e57838da7da98a628bd3754c05596af1b5487a371a75d0ffcf1a5c957b674098c9aa6fa7b7dcf8ae4670a491b3bcc6d0203010001028201003883a7d474be215ac05626bfc245a63ff4bcbd7b378acbffec2cb34c2ed74cd87df15b65e0a021a7d6a1dd51a68ce990eefa13c281cff2a44c2be31a118208b7a9b32a8531c405ca70e58723e1b2f3fe3acafed8175c8b603b06ef857c277bdb277bf1ffbdc34a9bb18a236cbfbc9a2655dfc4203ecb419d3796fd81131b30e31ff52aeee11a321b1767fb491ca0a4d49aa43f19fab2a6dfd198a14aadccc43c6fe869d7b91b70253ac6be3205a330216accacc6c3db86dfb4e7127ecdbdf81049bdaebee8016debc31dfab6299709460624f3332c1b04a6674dfa21d4438aadcebe09b7b55b7abafba3896a6c38bab550be86127d54375cee8573f2dd34141502818100f1dd06898de984245dea660cb779ed458e1cbbbede85db6c1eb448230cfcd3bd4aa6bdf05bed3ca58ee9b5e050807a9217f0a300196efef8501b514b1c7dc71c9fb0c8d29837fa8f8ba21106deaeb6a3f7216ab69b040cdc492f6fa61103cad158838958751a69765e8157e8cce487d8aaecfc2829a8d29c67d5cf7e8f6f028302818100c8f77a1475113c93d54777264431cf4dcbe85f635cba96f25733ccf1d7098752adbbc50a9dd27e738182fdc7528ddc7efea719878f3e3bb44ea7b0cae204a661e39a03cfa9ce20e175d6f261e17014846b9ba7bd7b486bfc1c4f843432b502be7ecca15b0c77886a1808bef9d60400b72b17e4286e4642cc93b64c1f8827024f028180396d7aa4e49e42b303dda91771e530726878e8173cecd999c57c96f84398308a6c9444db32689512d66925b73a46175462fccf2731e2ca0599b7b2c8bbde1d8ded58e38625807d2ce241bbfb3e9a8b61494794f800bca87511a782c2129e2ce52238313f60a6c1cdca48b9dfdbee9356ddd6e15483f7c2f24231615032ac70130281806fe07571d60a1673261476dc32b297f9733e957bb72f98c0a89309d0c82961d0412f7aee0216209724ce4b811f1022640057fdfa5d6003d4c8c4c9c2e8383677e040e9463dfda6885d15a031a552c3d9441e8f2f08e6b456d15be2f93c1150c9c3c51f3e949e26af095a3516d871ba043e553a8ad778fdceed9c5a9c632b743902818006bc41220c7afe7609b8bf28f9bc98595a0fd34dd18d0bf6715f35da854ce5c5804a82908fa7b6151c1f8c597138fe8e66d6912104982544cf82a4ca54bd533512bd62ea245084887760b9907c3650c20b73639ba771bf14573e024fd4e93ff34da2272754419a88490c2c07ffdb80bf507cef118d85680e9f97985e80d9d676',
        'WhF6YxeovufHTP7hF4FNJJrcJTUzIvZOjjZ2vMLMA9g=')

    try:
        currencies = await changelly_client.get_currencies()
        print("Currencies:", currencies)

        # # 2. Минимальный объём обмена (BTC -> ETH)
        # min_amount = await changelly_client.get_min_amount("btc", "eth")
        # print("Min amount BTC->ETH:", min_amount)

        # # 3. Расчёт конкретного количества ETH при обмене 0.01 BTC
        # exchange_amount = await changelly_client.get_exchange_amount("btc", "eth", 0.01)
        # print("Exchange amount for 0.01 BTC -> ETH:", exchange_amount)

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
        raise


if __name__ == "__main__":
    asyncio.run(main())

