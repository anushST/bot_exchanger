import sys
import os

# Добавляем путь к каталогу "src/api" в sys.path
base_path = os.path.join(os.path.dirname(__file__), "src", "api")
if base_path not in sys.path:
    sys.path.insert(0, base_path)
    
from easybit.schemas.account import AccountResponse
from easybit.schemas.rates import PairInfoResponse, RateResponse
from easybit.schemas.currencies_list import CurrencyListResponse
from easybit.schemas.order import OrderResponse, OrderStatusResponse, OrderStatusEnum



def test_currency_list_response():
    sample_currencies = {
        "success": 1,
        "data": [
            {
                "currency": "BTC",
                "name": "Bitcoin",
                "sendStatusAll": True,
                "receiveStatusAll": False,
                "networkList": [
                    {
                        "network": "BNB",
                        "name": "BEP2",
                        "isDefault": False,
                        "sendStatus": True,
                        "receiveStatus": False,
                        "receiveDecimals": 8,
                        "confirmationsMinimum": 1,
                        "confirmationsMaximum": 1,
                        "explorer": "https://explorer.binance.org/",
                        "explorerHash": "https://explorer.binance.org/tx/{{txid}}",
                        "explorerAddress": "https://explorer.binance.org/address/{{addr}}",
                        "hasTag": True,
                        "tagName": "MEMO",
                        "contractAddress": "BTCB-1DE",
                        "explorerContract": "https://binance.mintscan.io/assets/{{contr}}"
                    }
                ]
            }
        ]
    }
    currencies = CurrencyListResponse.parse_obj(sample_currencies)
    assert currencies.success == 1
    assert currencies.data[0].currency == "BTC"
    assert currencies.data[0].network_list[0].explorer_hash.startswith("https://explorer.binance.org/tx/")

def test_pair_info_response():
    sample_pair_info = {
        "success": 1,
        "data": {
            "minimumAmount": "0.01075",
            "maximumAmount": "420",
            "networkFee": "0.000005",
            "confirmations": 1,
            "processingTime": "3-5"
        }
    }
    pair_info = PairInfoResponse.parse_obj(sample_pair_info)
    assert pair_info.success == 1
    assert pair_info.data.minimum_amount == "0.01075"
    assert pair_info.data.processing_time == "3-5"

def test_rate_response():
    sample_rate = {
        "success": 1,
        "data": {
            "rate": "0.08195835",
            "sendAmount": "0.1",
            "receiveAmount": "0.00819083",
            "networkFee": "0.000005",
            "confirmations": 1,
            "processingTime": "3-5"
        }
    }
    rate = RateResponse.parse_obj(sample_rate)
    assert rate.success == 1
    assert rate.data.rate == "0.08195835"
    assert rate.data.receive_amount == "0.00819083"

def test_order_response():
    sample_order = {
        "success": 1,
        "data": {
            "id": "I1Y0EFP31Rwu",
            "send": "BTC",
            "receive": "ETH",
            "sendNetwork": "BTC",
            "receiveNetwork": "ETH",
            "sendAmount": "0.123",
            "receiveAmount": "1.73703678",
            "sendAddress": "1NiwKhcuV4Xrep5gnki4enFBBRH6hHuKzf",
            "sendTag": None,
            "receiveAddress": "0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf",
            "receiveTag": None,
            "refundAddress": None,
            "refundTag": None,
            "vpm": "off",
            "createdAt": 1643036313520
        }
    }
    order = OrderResponse.parse_obj(sample_order)
    assert order.success == 1
    assert order.data.send == "BTC"
    assert order.data.created_at == 1643036313520

def test_order_status_response():
    sample_order_status = {
        "success": 1,
        "data": {
            "id": "I1Y0EFP31Rwu",
            "status": "Awaiting Deposit",
            "receiveAmount": "1.73703678",
            "hashIn": None,
            "hashOut": None,
            "validationLink": None,
            "createdAt": 1643036313520,
            "updatedAt": 1643036313520
        }
    }
    order_status = OrderStatusResponse.parse_obj(sample_order_status)
    assert order_status.success == 1
    assert order_status.data.status == OrderStatusEnum.AWAITING_DEPOSIT
    assert order_status.data.receive_amount == "1.73703678"