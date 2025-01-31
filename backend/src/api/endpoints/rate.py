from fastapi import APIRouter, HTTPException

from src.api.ffio import ffio_redis_client
from src.models import RateTypes
from src.schemas import RatesSchemaResponse

router = APIRouter()


@router.get('/', response_model=RatesSchemaResponse)
async def get_rate(rate_type: RateTypes, from_coin: str, to_coin: str,
                   from_network: str, to_network: str):
    try:
        if rate_type == RateTypes.FIXED.value:
            rate = await ffio_redis_client.get_fixed_rate(
                from_coin, from_network, to_coin, to_network
            )
        elif rate_type == RateTypes.FLOAT.value:
            rate = await ffio_redis_client.get_float_rate(
                from_coin, from_network, to_coin, to_network
            )
        return RatesSchemaResponse(
            from_coin=rate.from_coin,
            to=rate.to_coin,
            in_amount=rate.in_amount,
            out=rate.out_amount,
            amount=rate.amount,
            tofee=rate.tofee,
            tofee_currency=rate.tofee_currency,
            minamount=rate.min_amount,
            maxamount=rate.max_amount,
        )
    except Exception:
        raise HTTPException(400, detail='Incorrect data')
