import logging
from decimal import Decimal, InvalidOperation

from src.api.changelly import changelly_client, schemas as changelly_schemas
from src.api.easybit import easybit_client, schemas as easybit_schemas
from src.api.coin_redis_data import coin_redis_data_client
from src.api.schemas import RatesSchema
from src.enums import Exchangers
from src.exceptions import ClientError
from src.redis import redis_client


logger = logging.getLogger(__name__)


def get_rate(rate_obj: RatesSchema) -> Decimal | None:
    try:
        if rate_obj.in_amount == 0:
            logger.warning("Cannot calculate rate: in_amount is zero")
            return None
        return rate_obj.out_amount / rate_obj.in_amount
    except (InvalidOperation, ZeroDivisionError, TypeError) as e:
        logger.error("Error calculating rate: %s", e)
        return None


async def get_fixed_best_rate(
        from_coin: str, from_coin_network: str,
        to_coin: str, to_coin_network: str) -> list[str, RatesSchema] | None:
    best_rate = None
    best_rate_obj = None
    exchanger = None

    try:
        cached_rate = await coin_redis_data_client.get_fixed_best_rate(
            from_coin, from_coin_network, to_coin, to_coin_network
        )
        if cached_rate:
            rate = get_rate(cached_rate[1])
            if rate:
                best_rate = rate
                best_rate_obj = cached_rate[1]
                exchanger = cached_rate[0]
    except ClientError as e:
        logger.error("Error getting cached fixed rate: %s", e, exc_info=True)
        # Continue execution to try getting rates from providers

    providers = [Exchangers.CHANGELLY, Exchangers.EASYBIT]

    for provider in providers:
        try:
            from_coin_info = await coin_redis_data_client.get_coin_full_info(
                provider, from_coin, from_coin_network
            )
            to_coin_info = await coin_redis_data_client.get_coin_full_info(
                provider, to_coin, to_coin_network
            )

            if not from_coin_info or not to_coin_info:
                continue

            if provider == Exchangers.CHANGELLY:
                try:
                    rate_obj = await changelly_client.get_fixed_rate(
                        changelly_schemas.CreateRate(
                            from_coin=from_coin_info.code,
                            to_coin=to_coin_info.code
                        )
                    )
                    
                    rate = get_rate(rate_obj)

                    if rate and (best_rate is None or rate > best_rate):
                        best_rate = rate
                        best_rate_obj = rate_obj
                        exchanger = provider.value
                except ClientError as e:
                    logger.error("Error getting fixed rate from Changelly: %s", e, exc_info=True)
                    continue
                    
            elif provider == Exchangers.EASYBIT:
                try:
                    rate_obj = await easybit_client.get_rate(
                        send=from_coin_info.code,
                        receive=to_coin_info.code,
                        amount=1.0  
                    )
                    
                    rate = get_rate(rate_obj)

                    if rate and (best_rate is None or rate > best_rate):
                        best_rate = rate
                        best_rate_obj = rate_obj
                        exchanger = provider.value
                except ClientError as e:
                    logger.error("Error getting rate from Easybit: %s", e, exc_info=True)
                    continue
                    
        except ClientError as e:
            logger.error("Error getting coin info for %s: %s", provider.value, e, exc_info=True)
            continue

    return [exchanger, best_rate_obj] if best_rate_obj else None


async def get_float_best_rate(
        from_coin: str, from_coin_network: str,
        to_coin: str, to_coin_network: str) -> list[str, RatesSchema] | None:
    best_rate = None
    best_rate_obj: RatesSchema = None
    exchanger = None

    try:
        cached_rate = await coin_redis_data_client.get_float_best_rate(
            from_coin, from_coin_network, to_coin, to_coin_network
        )
        if cached_rate:
            rate = get_rate(cached_rate[1])
            if rate:
                best_rate = rate
                best_rate_obj = cached_rate[1]
                exchanger = cached_rate[0]
    except ClientError as e:
        logger.error("Error getting cached float rate: %s", e, exc_info=True)
        # Continue execution to try getting rates from providers

    providers = [Exchangers.CHANGELLY, Exchangers.EASYBIT]

    for provider in providers:
        try:
            from_coin_info = await coin_redis_data_client.get_coin_full_info(
                provider, from_coin, from_coin_network
            )
            to_coin_info = await coin_redis_data_client.get_coin_full_info(
                provider, to_coin, to_coin_network
            )

            if not from_coin_info or not to_coin_info:
                continue

            if provider == Exchangers.CHANGELLY:
                try:
                    rate_obj = await changelly_client.get_float_rate(
                        changelly_schemas.CreateRate(
                            from_coin=from_coin_info.code,
                            to_coin=to_coin_info.code
                        )
                    )
                    
                    rate = get_rate(rate_obj)

                    if rate and (best_rate is None or rate > best_rate):
                        best_rate = rate
                        best_rate_obj = rate_obj
                        exchanger = provider.value
                except ClientError as e:
                    logger.error("Error getting float rate from Changelly: %s", e, exc_info=True)
                    continue
                    
            elif provider == Exchangers.EASYBIT:
                try:
                    rate_obj = await easybit_client.get_rate(
                        send=from_coin_info.code,
                        receive=to_coin_info.code,
                        amount=1.0 
                    )
                    
                    rate = get_rate(rate_obj)

                    if rate and (best_rate is None or rate > best_rate):
                        best_rate = rate
                        best_rate_obj = rate_obj
                        exchanger = provider.value
                except ClientError as e:
                    logger.error("Error getting rate from Easybit: %s", e, exc_info=True)
                    continue
                    
        except ClientError as e:
            logger.error("Error getting coin info for %s: %s", provider.value, e, exc_info=True)
            continue

    return [exchanger, best_rate_obj] if best_rate_obj else None


async def get_rate_in_usdt(
        from_coin: str, from_coin_network: str) -> RatesSchema | None:
    try:
        rate = await coin_redis_data_client.get_coin_in_usdt(
            from_coin, from_coin_network)
        if rate:
            return rate[1]

        networks_usdt = await coin_redis_data_client.get_networks('USDT')
        if not networks_usdt:
            return None
        
        providers = [Exchangers.CHANGELLY, Exchangers.EASYBIT]
        
        for net_usdt in networks_usdt:
            for provider in providers:
                try:
                    coin_info = await coin_redis_data_client.get_coin_full_info(
                        provider, from_coin, from_coin_network
                    )
                    usdt_info = await coin_redis_data_client.get_coin_full_info(
                        provider, 'USDT', net_usdt
                    )
                    
                    if not coin_info or not usdt_info:
                        continue

                    if provider == Exchangers.CHANGELLY:
                        try:
                            rate = await changelly_client.get_float_rate(
                                changelly_schemas.CreateRate(
                                    from_coin=coin_info.code,
                                    to_coin=usdt_info.code
                                )
                            )
                            if rate:
                                return rate
                        except ClientError as e:
                            logger.error("Error getting float rate to USDT from Changelly: %s", e, exc_info=True)
                            continue
                    elif provider == Exchangers.EASYBIT:
                        try:
                            rate = await easybit_client.get_rate(
                                send=coin_info.code,
                                receive=usdt_info.code,
                                amount=1.0
                            )
                            if rate:
                                return rate
                        except ClientError as e:
                            logger.error("Error getting rate to USDT from Easybit: %s", e, exc_info=True)
                            continue
                            
                except ClientError as e:
                    logger.error("Error getting coin info for %s: %s", provider.value, e, exc_info=True)
                    continue
        return None
    except ClientError as e:
        logger.error("Error getting rate in USDT: %s", e, exc_info=True)
        return None