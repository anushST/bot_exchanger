import json
import hmac
import hashlib
import requests


class FFioAPI:

    __api_url = "https://ff.io/api/v2/"

    def __init__(self, api_key, api_secret):
        self.__api_key = api_key
        self.__api_secret = api_secret

    def sign(self, query):
        return hmac.new(
            key=self.__api_secret.encode(),
            msg=json.dumps(query).encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

    def __query(self, endpoint, params=None):
        return requests.post(self.__api_url + endpoint, json=params, headers={
            "Accept": "application/json",
            "X-API-KEY": self.__api_key,
            "X-API-SIGN": self.sign(params or {}),
            "Content-Type": "application/json; charset=UTF-8"
        })

    def get_currencies(self):
        return self.__query("ccies").json()

    def get_rate(self, from_currency, to_currency, amount):
        return self.__query("price", {
            "type": "fixed",
            "fromCcy": from_currency,
            "toCcy": to_currency,
            "direction": "from",
            "amount": amount,
        }).json()



if __name__ == "__main__":

    api = FFioAPI(api_key="123", api_secret="123")
    result = api.get_currencies()
    print(result)

    result = api.get_rate("USDTTRC", "USDTSOL", 100)
    print(result)
