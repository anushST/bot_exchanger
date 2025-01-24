import logging

from fastapi import APIRouter, Request

from src.api.ffio.ffio_redis_data import ffio_redis_client
from src.core.db import get_async_session
from src.models import Transaction

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get('/')
async def get_currencies(request: Request):
    return await ffio_redis_client.get_coins()


@router.get('/info')
async def get_currency_info(coin: str, network: str):
    return await ffio_redis_client.get_coin_full_info(
        coin, network
    )


@router.get('/networks')
async def get_currency_networks(coin: str):
    return await ffio_redis_client.get_networks(coin)
