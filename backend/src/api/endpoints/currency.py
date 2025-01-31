import logging

from fastapi import APIRouter, Request

from src.api.ffio.ffio_redis_data import ffio_redis_client
from src.core.config import settings

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get('/')
async def get_currencies(request: Request):
    coins = await ffio_redis_client.get_coins()
    result = []
    for coin in coins:
        
        result.append({
            'name': coin,
            'url': f'https://{settings.DOMAIN}/coins/{coin}.png'
        })
    return result


@router.get('/info')
async def get_currency_info(coin: str, network: str):
    return await ffio_redis_client.get_coin_full_info(
        coin, network
    )


@router.get('/networks')
async def get_currency_networks(coin: str):
    return await ffio_redis_client.get_networks(coin)
