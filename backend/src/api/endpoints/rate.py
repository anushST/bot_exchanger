from fastapi import APIRouter, HTTPException
from src.api.ffio import ffio_redis_client
from enum import Enum
from src.api.ffio.schemas import RatesSchema

router = APIRouter()


class RateType(Enum):
    FIXED = 'fixed'
    FLOAT = 'float'


@router.get('/', response_model=RatesSchema)
async def get_rate(rate_type: RateType, from_coin: str, to_coin: str,
                   from_network: str, to_network: str):
    try:
        if rate_type == RateType.FIXED:
            return await ffio_redis_client.get_fixed_rate(
                from_coin, from_network, to_coin, to_network
            )
        elif rate_type == RateType.FLOAT:
            return await ffio_redis_client.get_float_rate(
                from_coin, from_network, to_coin, to_network
            )
    except Exception:
        raise HTTPException(400, detail='Incorrect data')
    raise HTTPException(400, detail='Invalid rate type')
