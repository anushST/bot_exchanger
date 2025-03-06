import asyncio
import base64
import binascii
import logging
import random

import aiohttp
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from pydantic import BaseModel

from . import schemas, constants as cnst
from src.api.schemas import RatesSchema
from src.api import exceptions as ex
from src.core.config import settings


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
            times = 0
            while times < 10:
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
                    logger.debug(f"Changelly API error: {response_data.error}")
                    if response_data.error.code == cnst.REQUEST_LIMIT_CODE:
                        await asyncio.sleep(1)
                        times += 1
                        continue
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
        if not response or response.error:
            return []
        pairs_info = response.result
        if pairs_info:
            return [schemas.PairParamsData(**p) for p in pairs_info]
        return []

    async def get_float_estimate(
            self, params: schemas.CreateFloatEstimate = None
            ) -> list[schemas.FloatEstimate]:
        response = await self._request(method='getExchangeAmount',
                                       params=params)
        if not response or response.error:
            return []
        estimate = response.result
        if estimate and isinstance(estimate, list):
            return [schemas.FloatEstimate(**x) for x in estimate]
        return []

    async def get_fixed_estimate(
            self, params: schemas.CreateFixedEstimate
            ) -> list[schemas.FixedEstimate]:
        response = await self._request(method='getFixRateForAmount',
                                       params=params)
        print(response)
        if not response or response.error:
            return []
        estimate = response.result
        if estimate and isinstance(estimate, list):
            return [schemas.FixedEstimate(**x) for x in estimate]
        return []

    async def get_float_rate(
            self, params: schemas.CreateRate) -> RatesSchema | None:
        get_datas = await self.get_pairs_params(schemas.PairParams(
            from_coin=params.from_coin, to_coin=params.to_coin
        ))
        if not get_datas:
            return None
        data = get_datas[0]
        amount_from = random.uniform(float(data.min_amount_float),
                                     float(data.max_amount_float))
        estimate = await self.get_float_estimate(schemas.CreateFloatEstimate(
            from_coin=params.from_coin, to_coin=params.to_coin,
            amount_from=amount_from
        ))
        if not estimate:
            return None
        estimate = estimate[0]
        return RatesSchema(
            from_coin=estimate.from_,
            to_coin=estimate.to,
            in_amount=estimate.amount_from,
            out_amount=estimate.amount_to,
            to_network_fee=estimate.network_fee,
            min_from_amount=estimate.min_from,
            min_to_amount=estimate.min_to,
            max_from_amount=estimate.max_from,
            max_to_amount=estimate.max_to
        )

    async def get_fixed_rate(
            self, params: schemas.CreateRate) -> RatesSchema | None:
        get_datas = await self.get_pairs_params(schemas.PairParams(
            from_coin=params.from_coin, to_coin=params.to_coin
        ))
        if not get_datas:
            return None
        data = get_datas[0]
        amount_from = random.uniform(float(data.min_amount_fixed),
                                     float(data.max_amount_fixed))
        estimate = await self.get_fixed_estimate(schemas.CreateFixedEstimate(
            from_coin=params.from_coin, to_coin=params.to_coin,
            amount_from=amount_from
        ))
        if not estimate:
            return None
        estimate = estimate[0]
        return RatesSchema(
            from_coin=estimate.from_,
            to_coin=estimate.to,
            in_amount=estimate.amount_from,
            out_amount=estimate.amount_to,
            to_network_fee=estimate.network_fee,
            min_from_amount=estimate.min_from,
            min_to_amount=estimate.min_to,
            max_from_amount=estimate.max_from,
            max_to_amount=estimate.max_to
        )

    async def create_float_transaction(
            self, params: schemas.CreateFloatTransaction
            ) -> schemas.FloatTransaction:
        response = await self._request('createTransaction', params)
        if response.error:
            error_code = response.error.code
            if error_code == cnst.INVALID_ADDRESS_CODE:
                raise ex.InvalidAddressError('Address is invalid')
            else:
                raise ex.ClientError('Some error occured')
        print(response)
        return schemas.FloatTransaction(**response.result)

    async def create_fixed_transaction(
            self, params: schemas.CreateFixedTransaction
            ) -> schemas.FixedTransaction:
        response = await self._request('createFixTransaction', params)
        if response.error:
            error_code = response.error.code
            if error_code == cnst.INVALID_ADDRESS_CODE:
                raise ex.InvalidAddressError('Address is invalid')
            else:
                raise ex.ClientError('Some error occured')
        print(response)
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
    settings.CHANGELLY_PRIVATE_KEY, settings.CHANGELLY_X_API_KEY
)
