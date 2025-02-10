import asyncio
import base64
import binascii
import logging

import aiohttp
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from pydantic import BaseModel

from . import schemas
from src.api.ffio.schemas import OrderType
from src.transaction.schemas import CreateBestPrice, BestPrice
from .changelly_redis_data import changelly_redis_client


logger = logging.getLogger(__name__)


class ChangellyClient:

    def __init__(self, private_key: str, x_api_key: str) -> None:
        self.private_key = private_key
        self.x_api_key = x_api_key

    def _sign_request(self, body: str) -> bytes:
        decoded_private_key = binascii.unhexlify(self.private_key)
        private_key = RSA.import_key(decoded_private_key)
        message = body.encode('utf-8')
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

    async def _request(self, method: str, params: BaseModel = None
                       ) -> schemas.JsonRPCResponse:
        if params is None:
            params = {}

        rpc_request = schemas.JsonRPCRequest(method=method, params=params)

        headers = self._get_headers(rpc_request.model_dump_json(
            by_alias=True, exclude_none=True))
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.changelly.com/v2/',
                headers=headers,
                data=rpc_request.model_dump_json(
                    by_alias=True, exclude_none=True)
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Changelly API error (HTTP {response.status}): {text}") # noqa
                data = await response.json()
                response_data = schemas.JsonRPCResponse(**data)

        if response_data.error:
            pass  # ToDO

        return response_data

    async def get_currencies_list(self) -> list[str]:
        response = await self._request(method="getCurrencies")
        if response.result:
            return response.result
        return []

    async def get_currencies_full(self) -> list[schemas.Coin]:
        response = await self._request(method="getCurrenciesFull")
        coins_data = response.result
        if coins_data:
            return [schemas.Coin(**coin) for coin in coins_data]
        return []

    async def get_pairs(self) -> list[schemas.CoinPairs]:
        response = await self._request(method='getPairs')
        pairs_data = response.result
        if pairs_data:
            return [schemas.CoinPairs(**pair) for pair in pairs_data]
        return []

    async def get_pairs_params(
            self, params: schemas.PairParams) -> list[schemas.PairParamsData]:
        response = await self._request(method='getPairsParams', params=params)
        pairs_info = response.result
        if pairs_info:
            return [schemas.PairParamsData(**p) for p in pairs_info]
        return []

    async def get_float_estimate(
            self, params: schemas.CreateFloatEstimate = None
            ) -> schemas.FloatEstimate:
        response = await self._request(method='getExchangeAmount',
                                       params=params)
        estimate = response.result
        if estimate and isinstance(estimate, list):
            return [schemas.FloatEstimate(**x) for x in estimate]
        return []

    async def get_float_estimates(self):
        rate_pairs = await self.get_pairs()
        estimates = []
        for rate in rate_pairs:
            estimates.append(
                schemas.CreateFloatEstimate(
                    from_coin=rate.from_coin,
                    to=rate.to_coin,
                    amountFrom=1
                )
            )
        response = await self._request(method='getExchangeAmount',
                                       params=estimates)
        estimate = response.result
        if estimate and isinstance(estimate, list):
            return [schemas.FloatEstimate(**x) for x in estimate]
        return []

    async def get_fixed_estimates(self):
        rate_pairs = await self.get_pairs()
        estimates = []
        for rate in rate_pairs:
            estimates.append(
                schemas.CreateFixedEstimate(
                    from_coin=rate.from_coin,
                    to=rate.to_coin,
                    amountFrom=1
                )
            )
        print(estimates)
        response = await self._request(method='getFixRateForAmount',
                                       params=estimates)
        estimate = response.result
        if estimate and isinstance(estimate, list):
            return [schemas.FixedEstimate(**x) for x in estimate]
        return []

    async def get_fixed_estimate(
            self, params: schemas.CreateFixedEstimate
            ) -> schemas.FixedEstimate:
        response = await self._request(method='getFixRateForAmount',
                                       params=params)
        print(response)
        estimate = response.result
        if estimate and isinstance(estimate, list):
            return [schemas.FixedEstimate(**x) for x in estimate]
        return []

    async def get_rate(self, data: CreateBestPrice = None):
        from_ccy = await changelly_redis_client.get_coin_full_info(
            data.from_currency, data.from_network
        )
        to_ccy = await changelly_redis_client.get_coin_full_info(
            data.to_currency, data.to_network
        )
        if data.type == OrderType.fixed:
            result = await self.get_fixed_estimate(schemas.CreateFixedEstimate(
                from_coin=from_ccy.code, to=to_ccy.code, amountFrom=data.amount
            ))
        elif data.type == OrderType.float:
            result = await self.get_float_estimate(schemas.CreateFloatEstimate(
                from_coin=from_ccy.code, to=to_ccy.code, amountFrom=data.amount
            ))

        return BestPrice(
            exchanger='changelly',
            from_amount=result[0].amount_from,
            to_amount=result[0].amount_to,
            **data.model_dump()
        )

    async def create_float_transaction(
            self, params: schemas.CreateFloatTransaction
            ) -> schemas.FloatTransaction:
        response = await self._request('createTransaction', params)
        print(response)
        return schemas.FloatTransaction(**response.result)

    async def create_fixed_transaction(
            self, params: schemas.CreateFixedTransaction
            ) -> schemas.FixedTransaction:
        response = await self._request('createFixTransaction', params)
        return schemas.FixedTransaction(**response.result)

    async def get_transaction_details(
            self, params: schemas.CreateTransactionDetails
            ) -> schemas.TransactionDetails:
        response = await self._request('getTransactions', params)
        data = response.result
        if data and isinstance(data, list):
            return [schemas.TransactionDetails(**x) for x in data]
        return []

changelly_client = ChangellyClient(
        '308204be020100300d06092a864886f70d0101010500048204a8308204a40201000282010100b1bc33122b1931b6b76ce76f7171c8db121598fbd95747e7c9ed0a0ab1c9b328d2c80bd0874ecc8de73dcc355296f54dc46f2c8a202798bbaa502a1e2a038e44ed2c369f670e9b7f642eb85d0f65b610e7a4b57cabedc69754e0c444c0411b7d49db3fb3c0e7b7d4cff6225a374d3124a1c48704772a2e0a80dd983bd595d0e326307013f0303dbc772ff47ba4325fe35c7f5f10aa6d2d8eaae45034dd2f025159a2aa7d8dddf6a5cc8c86b8a33cc27f606807692cdb5f696be4c65e317cfa4309e7e42b3649a87ea219624348bdb321083457ddd1d2cde5fa34e8b6a8b0873f7027f32262d2d8bfe98c8f5820ef42d4d3dbd7c4b9956952c7aaf288f2d0bd670203010001028201003c0ddb33c85c3af0020a4a28ddac14b1f0ea5b46bda940229198064c96c610433af55d0898af876e6b33f64c0e1bf3c6d318bd73ee6972b1f65a1fe11151224127e2489293bfdbcaaf8f19bc57f7860d3037f71aa8fd2e9cf390fec03c35c39411e08325b9889214d62fd46ba743edd6f2d1f4cd0d76b317d973067d312dede64223afc01506d0eb742a2d1d1dc2a989364709b4b41ed7c3de7df67967ca449d018064858527210f9d860ec3fbf09ab44f2ea38cd4b921acdba68f83321765e9b075e1d7a8cbfc1d53ab6087660849d0532fe819a1f06167fb72f5d0799ca48c2d1f8f277946082fbfa785ec16b772e254af30696cf7ecd5019773d6fcfab80102818100e14bcc0db1bd5face75b41e5f9baf0ed28a237220affc32e64a4d109cb18941e394d559ac00d9745da57e081b092a98b31d517a7ac35e5914de61a71f3182ad4d880884fd97b1e829b912d7ea3a0fd2145cf72abcba8c6f1172f26d6dbe194d1aa00a6af20360b4a244c0687bb69af5dd3af18b208abd616fa85b89ffd9e3da902818100c9f514d02d5a0336b788d83c03a00af0a7d67f49a75714e358b955d5a2529670774cc0d739522682bcaef544245e5e138341b3e0aac03908fafee99723735498d8fe15694c1e05114cb86f5f3477e749699af61a3b51f137e1f89c19b3dee0331e6f1c46c50bc4b3171c373335c222b452d6dc624248b8d17610a1b261c16c8f02818100be7b8970e2a00c6e71c59477cea721e04204b4bc91b420dfeeb3f31166a7c743ae8b161f9ad562daea7a7614f0a76fb582527a878770a242322ca49b473f5da74bcd9072829c37f591763392e8e1ca6301551dcce68a3279d0724b5249e1f62336ab0a42f2e6feb096f3b869b628eade5785a9498d4f4bd96dc2f5903fac34d102818100c9bea5f80015f737e5c8321a6194b2d90d10dd3efa87a73a251b9f7f3614426c3f00d1732eb3bdfcc3f812d2eb71c990bc8219eac92814d1bfca7e16993750bf0fa5624639df933860e7ad79f1b405bbf45ef491e7c847ab87750e9b2e6fea8fa64b6077e1c78bcb4bbec7f5c43216f103ffd74fe0df3ca121cc237b4ae42a490281801f88aba9a0baffbb43ada04e7a99fc9209650aecce51ade69acc4b5cede94a950c6a7dac5bc25304bd9920644c6230867a136f4e04c99528f22f6678631768ea1ef3538ecd8fa27aeddd31395983ded7c20f494653f47bc88168474001d8f23bd61cfce4eb53aa7d81c7eca927936be413684dbff2a9ec9ad8de46d3dc8438cb',
        'MwLlkpKuXnXLjPT4x+7J7rlPv5O8Rg0IXxv25A1IRMs=')

async def main():
    try:
        currencies = await changelly_client.create_float_transaction(
            schemas.CreateFloatTransaction(
                from_='usdtbsc',
                to='ton',
                amount_from='35',
                address='EQD5mxRgCuRNLxKxeOjG6r14iSroLF5FtomPnet-sgP5xNJb'
            )
        )
        currencies = await changelly_client.get_transaction_details(
            schemas.CreateTransactionDetails(
                id_='msnhnmmfd8p59trc'
            )
        )
        print(currencies)

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
    except Exception:
        raise


if __name__ == "__main__":
    asyncio.run(main())
