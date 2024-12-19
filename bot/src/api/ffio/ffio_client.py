import asyncio
import hashlib
import hmac
import json
import logging
from decimal import Decimal

import aiohttp
import xmltodict
from pydantic import BaseModel

from . import schemas
from src.config import config

logger = logging.getLogger(__name__)


class FFIOClient:
    RESP_OK = 0
    FIXED_RATES_URL = 'https://ff.io/rates/fixed.xml'
    FLOAT_RATES_URL = 'https://ff.io/rates/float.xml'

    def __init__(self, key: str, secret: str) -> None:
        self.key = key
        self.secret = secret

    def _sign(self, data: str) -> hmac.HMAC:
        return hmac.new(self.secret.encode(), data.encode(),
                        hashlib.sha256).hexdigest()

    async def _req(self, method: str, data: BaseModel = None) -> list[dict]:
        url = f'https://ff.io/api/v2/{method}'
        req = data.model_dump_json(by_alias=True) if data else json.dumps({})

        headers = {
            'Accept': 'application/json',
            'X-API-KEY': self.key,
            'X-API-SIGN': self._sign(req),
            'Content-Type': 'application/json; charset=UTF-8',
        }

        async with aiohttp.ClientSession() as session:
            retry_times = 0
            while retry_times < 90:
                async with session.post(
                        url, data=req, headers=headers) as response:
                    result = await response.json()
                    if retry_times == 30:
                        logger.warning('Retried about 30 times, error.')
                    if response.status != 200:
                        raise Exception(f'HTTP Error: {response.status}')

                    if result['code'] == self.RESP_OK:
                        return result['data']
                    elif result['code'] == 429:
                        await asyncio.sleep(1)
                        retry_times += 1
                        continue
                    else:
                        raise Exception(result['msg'], result['code'])

    async def _get_rates(self, is_fixed=True) -> list[schemas.RatesSchema]:
        async with aiohttp.ClientSession() as session:
            url = self.FIXED_RATES_URL if is_fixed else self.FLOAT_RATES_URL
            async with session.get(url) as response:
                xml_data = await response.text()
                dict_data = xmltodict.parse(xml_data)

        rates = dict_data['rates']['item']
        results = []
        for rate in rates:
            if 'tofee' in rate:
                tofee, tofee_cur = rate['tofee'].split()
            else:
                tofee, tofee_cur = (None, None)
            results.append(
                schemas.RatesSchema(
                    from_coin=rate['from'],
                    to=rate['to'],
                    in_amount=Decimal(rate['in']),
                    out=Decimal(rate['out']),
                    amount=Decimal(rate['amount']),
                    tofee=Decimal(tofee) if tofee else None,
                    tofee_currency=tofee_cur,
                    minamount=Decimal(rate['minamount'].split()[0]),
                    maxamount=Decimal(rate['maxamount'].split()[0])
                )
            )
        return results

    async def get_fixed_rates(self) -> list[schemas.RatesSchema]:
        return await self._get_rates(True)

    async def get_float_rates(self) -> list[schemas.RatesSchema]:
        return await self._get_rates(False)

    async def ccies(self) -> list[schemas.Currency]:
        currencies = await self._req('ccies', )
        result = []
        for cur in currencies:
            result.append(schemas.Currency(**cur))
        return result

    async def price(self, data: dict) -> dict:  # ToDo
        return await self._req('price', data)

    async def create(self, data: schemas.CreateOrder) -> schemas.OrderData:
        order_data = await self._req('create', data)
        logger.info(f'Order data: {order_data}')
        return schemas.OrderData(**order_data)

    async def order(
            self, data: schemas.CreateOrderDetails) -> schemas.OrderData:
        order_data = await self._req('order', data)
        return schemas.OrderData(**order_data)

    async def emergency(self, data: dict) -> dict:  # ToDo
        return await self._req('emergency', data)

    async def qr(self, data: dict) -> dict:  # ToDo
        return await self._req('qr', data)


ffio_client = FFIOClient(config.FFIO_APIKEY, config.FFIO_SECRET)


async def main():
    Api = FFIOClient('rOSLgo318f85Tfz6ODeKScpicdE5dDuJY2gttlc6',
                        'Qa3wT7MtTeC0NjZavuAqgxGfxZqD76F2CZPYF6qh')
    body = schemas.CreateOrder(
        type='fixed',
        fromCcy='BSC',
        toCcy='BTC',
        direction='from',
        amount=Decimal('0.1'),
        toAddress='1BfCNvssYq4JqMqHQVL5w6WwRjWpRoR4Pw',
    )
    body = schemas.CreateOrderDetails(token='GJbuNg86bnG2fbkaPnZxsasQ1xkUt90NYLNS9AHv', id='YYCSH7')
    body = {
        'type': 'fixed',
        'fromCcy': 'BSC',
        'toCcy': 'BTC',
        'direction': 'from',
        'amount': '1'
    }
    results = await Api.price(body)
    print(results)

if __name__ == '__main__':
    asyncio.run(main())
