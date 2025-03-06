import logging

from fastapi import APIRouter, HTTPException

from src.api import rate_data
from src.api.schemas import RatesSchema
from src.models import RateTypes

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get('/', response_model=RatesSchema)
async def get_rate(rate_type: RateTypes, from_coin: str, to_coin: str,
                   from_network: str, to_network: str):
    try:
        if rate_type == RateTypes.FIXED:
            rate = await rate_data.get_fixed_best_rate(
                from_coin, from_network, to_coin, to_network
            )
        elif rate_type == RateTypes.FLOAT:
            rate = await rate_data.get_float_best_rate(
                from_coin, from_network, to_coin, to_network
            )
    except Exception as e:
        logger.error(e, exc_info=True)
        raise HTTPException(500, detail='Some Error while processing')

    if not rate:
        raise HTTPException(
            400, detail='This pair is not available now for exchange')
    return rate[1]


@router.get('/in-usdt', response_model=RatesSchema)
async def get_rate_in_usdt(coin: str, network: str):
    return await rate_data.get_rate_in_usdt(coin, network)
