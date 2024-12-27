import asyncio
import hashlib
import hmac
import json
import logging
from decimal import Decimal
from typing import Optional

import aiohttp
import xmltodict
from aiohttp import ClientError, ClientTimeout
from pydantic import BaseModel

from . import schemas, constants as c
from src.api import exceptions as ex
from src.config import config

logger = logging.getLogger(__name__)


class FFIOClient:
    RESP_OK = 0
    FIXED_RATES_URL = 'https://ff.io/rates/fixed.xml'
    FLOAT_RATES_URL = 'https://ff.io/rates/float.xml'

    def __init__(self, key: str, secret: str, timeout: int = 10) -> None:
        self.key = key
        self.secret = secret
        self.timeout = ClientTimeout(total=timeout)

    def _sign(self, data: str) -> str:
        return hmac.new(self.secret.encode(), data.encode(),
                        hashlib.sha256).hexdigest()

    async def _req(self, method: str,
                   data: Optional[BaseModel] = None) -> list[dict]:
        url = f'https://ff.io/api/v2/{method}'
        logger.info(f'Sending request to {url} with data: {data}')
        req = data.model_dump_json(by_alias=True) if data else json.dumps({})

        headers = {
            'Accept': 'application/json',
            'X-API-KEY': self.key,
            'X-API-SIGN': self._sign(req),
            'Content-Type': 'application/json; charset=UTF-8',
        }

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            retry_times = 1
            while retry_times < c.RETRY_TIMES:
                try:
                    async with session.post(
                            url, data=req, headers=headers) as response:
                        result = await response.json()
                        if result.get('code') == 429:
                            logger.warning(
                                f'Request limit exceeded. Retrying... ({result.get('msg')})') # noqa
                            await asyncio.sleep(retry_times)
                            retry_times += 1
                            continue
                        return result
                except ClientError as e:
                    raise ex.NetworkError('Network error occurred') from e
                except asyncio.TimeoutError:
                    raise ex.TimeoutError('Request timed out')
                except json.JSONDecodeError as e:
                    raise ex.DataProcessingError(
                        'Failed to decode JSON response') from e
            raise ex.MaximumRetriesError('Maximum retries happened.')

    async def _get_rates(self, is_fixed=True) -> list[schemas.RatesSchema]:
        url = self.FIXED_RATES_URL if is_fixed else self.FLOAT_RATES_URL
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    xml_data = await response.text()
                    dict_data = xmltodict.parse(xml_data)

            rates = dict_data['rates']['item']
            results = []
            for rate in rates:
                tofee, tofee_cur = rate.get('tofee', '0 None').split()
                results.append(
                    schemas.RatesSchema(
                        from_coin=rate['from'],
                        to=rate['to'],
                        in_amount=Decimal(rate['in']),
                        out=Decimal(rate['out']),
                        amount=Decimal(rate['amount']),
                        tofee=Decimal(tofee) if tofee != 'None' else None,
                        tofee_currency=tofee_cur,
                        minamount=Decimal(rate['minamount'].split()[0]),
                        maxamount=Decimal(rate['maxamount'].split()[0])
                    )
                )
            return results
        except ClientError as e:
            raise ex.NetworkError(
                'Network error occurred while fetching rates') from e
        except asyncio.TimeoutError:
            raise ex.TimeoutError('Request timed out')
        except xmltodict.expat.ExpatError as e:
            raise ex.DataProcessingError('Error parsing XML response') from e

    async def get_fixed_rates(self) -> list[schemas.RatesSchema]:
        return await self._get_rates(True)

    async def get_float_rates(self) -> list[schemas.RatesSchema]:
        return await self._get_rates(False)

    async def ccies(self) -> list[schemas.Currency]:
        currencies = await self._req('ccies')
        return [schemas.Currency(**cur) for cur in currencies['data']]

    async def create(self, data: schemas.CreateOrder) -> schemas.OrderData:
        response = await self._req('create', data)
        logger.info(response)
        response_code = response.get('code')
        response_message = response.get('msg')
        if response_code == 301:
            if response_message == c.INVALID_ADDRESS_MESSAGE:
                raise ex.InvalidAddressError('Your address is invalid')
            elif response_message == c.OUT_OF_LIMITIS_MESSAGE:
                raise ex.OutOFLimitisError('Amount is out of limits')
            elif response_message == c.INCORRECT_DIRECTION_MESSAGE:
                raise ex.IncorrectDirectionError(c.INCORRECT_DIRECTION_MESSAGE)
        elif response_code == 300:
            if response_message == c.PARTNET_INTERNAL_ERROR_MESSAGE:
                raise ex.PartnerInternalError(c.PARTNET_INTERNAL_ERROR_MESSAGE)
        return schemas.OrderData(**response['data'])

    async def order(
            self, data: schemas.CreateOrderDetails) -> schemas.OrderData:
        response = await self._req('order', data)
        return schemas.OrderData(**response['data'])

    async def emergency(self, data: schemas.CreateEmergency) -> bool:
        response = await self._req('emergency', data)
        response_code = response.get('code')
        response_message = response.get('msg')
        if response_code == 301:
            if response_message == c.INVALID_ADDRESS_MESSAGE:
                logger.info('Your address is invalid')
                raise ex.InvalidAddressError('Your address is invalid')
        return response


ffio_client = FFIOClient(config.FFIO_APIKEY, config.FFIO_SECRET)
