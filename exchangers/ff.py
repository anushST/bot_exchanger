import hashlib
import hmac
import json
import requests

# from ..config import FFIO_APIKEY, FFIO_SECRET


class FixedFloatApi:
    RESP_OK = 0
    TYPE_FIXED = 'fixed'
    TYPE_FLOAT = 'float'

    def __init__(self, key: str, secret: str) -> None:
        self.key = key
        self.secret = secret

    def _sign(self, data: str) -> hmac.HMAC:
        return hmac.new(self.secret.encode(), data.encode(),
                        hashlib.sha256).hexdigest()

    def _req(self, method: str, data: dict) -> dict:
        url = f'https://ff.io/api/v2/{method}'
        req = json.dumps(data)

        headers = {
            'Accept': 'application/json',
            'X-API-KEY': self.key,
            'X-API-SIGN': self._sign(req),
            'Content-Type': 'application/json; charset=UTF-8',
        }

        response = requests.post(url, data=req, headers=headers)
        if response.status_code != 200:
            raise Exception(f'HTTP Error: {response.status_code}')

        result = response.json()
        print(result)
        if result['code'] == self.RESP_OK:
            return result['data']
        else:
            raise Exception(result['msg'], result['code'])

    def ccies(self) -> dict:
        return self._req('ccies', {})

    def price(self, data: dict) -> dict:
        return self._req('price', data)

    def create(self, data: dict) -> dict:
        return self._req('create', data)

    def order(self, data: dict) -> dict:
        return self._req('order', data)

    def emergency(self, data: dict) -> dict:
        return self._req('emergency', data)

    def set_email(self, data: dict) -> dict:
        return self._req('setEmail', data)

    def qr(self, data: dict) -> dict:
        return self._req('qr', data)


if __name__ == '__main__':
    Api = FixedFloatApi('rOSLgo318f85Tfz6ODeKScpicdE5dDuJY2gttlc6',
                        'Qa3wT7MtTeC0NjZavuAqgxGfxZqD76F2CZPYF6qh')
    data = {
        'type': 'fixed',
        'fromCcy': 'BSC',
        'toCcy': 'BTC',
        'direction': 'from',
        'amount': '0.019958',
        'toAddress': '1BfCNvssYq4JqMqHQVL5w6WwRjWpRoR4Pw',
    }
    data = {
        'id': 'W8MCXU',
        'token': 'kcjm7QmZknYnppnm26aM1LTRldVp8ATYtJgZrsoZ'
    }
    data = {
        'id': 'UFAZMB',
        'token': 'aARonG6Dqr0tz5FqARhZT4Nu62SENasIloaaviT3',
        'choice': 'REFUND',
        'address': '0x2ace0222ebc017c81549af01777b450232601fe3'
    }
    response = Api.emergency(data)

    from pprint import pprint
    pprint(response)
