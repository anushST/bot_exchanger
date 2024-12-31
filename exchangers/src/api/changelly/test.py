import base64
import binascii
import json
import logging
from typing import List

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from requests import post, Response

logging.basicConfig(level=logging.INFO)


class ApiException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class ApiService:
    def __init__(self, url: str, private_key: str, x_api_key: str):
        self.url = url
        self.private_key = private_key
        self.x_api_key = x_api_key

    def _request(self, method: str, params: dict or list = None) -> Response or List[dict]:
        params = params if params else {}
        message = {
            'jsonrpc': '2.0',
            'id': 'test',
            'method': method,
            'params': params
        }
        response = post(self.url, headers=self._get_headers(body=message), json=message)
        if response.ok:
            response_body = response.json()
            logging.info(f'{method} response: {response_body} (request: {params})')
            if response_body.get('error'):
                error = response_body['error']
                raise ApiException(error['code'], error['message'])
            return response_body['result']
        raise ApiException(response.status_code, response.text)

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
            'content-type': 'application/json',
            'X-Api-Key': self.x_api_key,
            'X-Api-Signature': signature,
        }

    def get_pairs_params(self, currency_from: str, currency_to: str):
        return self._request('getPairsParams', params=[{'from': currency_from, 'to': currency_to}])


api = ApiService(
    'https://api.changelly.com/v2/',
    '308204bc020100300d06092a864886f70d0101010500048204a6308204a20201000282010100bdde7cb36e92b8d10d9ef3f036746988b1b384e6ac05df9173316de50519275410fad574eae2690388b41b2f7e018cd3815f1d99e4c2f7f56171c20e78580254fe43f4d2d1cee2d52272e23054eb829b7f5a749a775a784cd48983e22dddbf70d71bc6914621e3c56b2d682585ae368044f3c17ad5b901db4bd7e8b18aea696b36e3ebcc2424c02f6ba72bc1f304ee0dee67c3da31a7544f2a2d413babfe4c613ef604358ee64a7e748b1bc9636c4668693b89d03a1d7531ecf991572112e37a4f8f19b3e4829f3789d9423f0fa35d865e57838da7da98a628bd3754c05596af1b5487a371a75d0ffcf1a5c957b674098c9aa6fa7b7dcf8ae4670a491b3bcc6d0203010001028201003883a7d474be215ac05626bfc245a63ff4bcbd7b378acbffec2cb34c2ed74cd87df15b65e0a021a7d6a1dd51a68ce990eefa13c281cff2a44c2be31a118208b7a9b32a8531c405ca70e58723e1b2f3fe3acafed8175c8b603b06ef857c277bdb277bf1ffbdc34a9bb18a236cbfbc9a2655dfc4203ecb419d3796fd81131b30e31ff52aeee11a321b1767fb491ca0a4d49aa43f19fab2a6dfd198a14aadccc43c6fe869d7b91b70253ac6be3205a330216accacc6c3db86dfb4e7127ecdbdf81049bdaebee8016debc31dfab6299709460624f3332c1b04a6674dfa21d4438aadcebe09b7b55b7abafba3896a6c38bab550be86127d54375cee8573f2dd34141502818100f1dd06898de984245dea660cb779ed458e1cbbbede85db6c1eb448230cfcd3bd4aa6bdf05bed3ca58ee9b5e050807a9217f0a300196efef8501b514b1c7dc71c9fb0c8d29837fa8f8ba21106deaeb6a3f7216ab69b040cdc492f6fa61103cad158838958751a69765e8157e8cce487d8aaecfc2829a8d29c67d5cf7e8f6f028302818100c8f77a1475113c93d54777264431cf4dcbe85f635cba96f25733ccf1d7098752adbbc50a9dd27e738182fdc7528ddc7efea719878f3e3bb44ea7b0cae204a661e39a03cfa9ce20e175d6f261e17014846b9ba7bd7b486bfc1c4f843432b502be7ecca15b0c77886a1808bef9d60400b72b17e4286e4642cc93b64c1f8827024f028180396d7aa4e49e42b303dda91771e530726878e8173cecd999c57c96f84398308a6c9444db32689512d66925b73a46175462fccf2731e2ca0599b7b2c8bbde1d8ded58e38625807d2ce241bbfb3e9a8b61494794f800bca87511a782c2129e2ce52238313f60a6c1cdca48b9dfdbee9356ddd6e15483f7c2f24231615032ac70130281806fe07571d60a1673261476dc32b297f9733e957bb72f98c0a89309d0c82961d0412f7aee0216209724ce4b811f1022640057fdfa5d6003d4c8c4c9c2e8383677e040e9463dfda6885d15a031a552c3d9441e8f2f08e6b456d15be2f93c1150c9c3c51f3e949e26af095a3516d871ba043e553a8ad778fdceed9c5a9c632b743902818006bc41220c7afe7609b8bf28f9bc98595a0fd34dd18d0bf6715f35da854ce5c5804a82908fa7b6151c1f8c597138fe8e66d6912104982544cf82a4ca54bd533512bd62ea245084887760b9907c3650c20b73639ba771bf14573e024fd4e93ff34da2272754419a88490c2c07ffdb80bf507cef118d85680e9f97985e80d9d676',
    'WhF6YxeovufHTP7hF4FNJJrcJTUzIvZOjjZ2vMLMA9g='
)
print(api.get_pairs_params('eth', 'btc'))
