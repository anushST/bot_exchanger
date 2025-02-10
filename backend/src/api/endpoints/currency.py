import logging

from fastapi import APIRouter, Request

from .currency_data import currency_name
from src.api.coin_redis_data import coin_redis_data_client
from src.core.config import settings

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get('/')
async def get_currencies(request: Request):
    coins = await coin_redis_data_client.get_coins()
    result = []
    for coin in coins:
        result.append({
            'name': coin,
            'url': f'https://{settings.DOMAIN}/coins/{coin}.png',
            'full_name': currency_name.get(coin)
        })
    return result


@router.get('/info')
async def get_currency_info(coin: str, network: str):
    return await coin_redis_data_client.get_coin_info(
        coin, network
    )


@router.get('/networks')
async def get_currency_networks(coin: str):
    networks = await coin_redis_data_client.get_networks(coin)
    result = []
    for net in networks:
        result.append({
            'name': net,
            'url': f'https://{settings.DOMAIN}/coins/{net}.png',
        })
    return result
