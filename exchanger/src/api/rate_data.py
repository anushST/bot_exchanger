import logging
from decimal import Decimal

from src.api.changelly import changelly_client, schemas as changelly_schemas
from src.api.coin_redis_data import coin_redis_data_client
from src.api.schemas import RatesSchema
from src.enums import Exchangers


logger = logging.getLogger(__name__)


def get_rate(rate_obj: RatesSchema) -> Decimal:
    return rate_obj.out_amount / rate_obj.in_amount


async def get_fixed_best_rate(
        from_coin: str, from_coin_network: str,
        to_coin: str, to_coin_network: str) -> list[str, RatesSchema] | None:
    best_rate = None
    best_rate_obj = None
    exchanger = None

    cached_rate = await coin_redis_data_client.get_fixed_best_rate(
        from_coin, from_coin_network, to_coin, to_coin_network
    )
    if cached_rate:
        best_rate = get_rate(cached_rate[1])
        best_rate_obj = cached_rate[1]
        exchanger = cached_rate[0]

    providers = [Exchangers.CHANGELLY]

    for provider in providers:
        from_coin_info = await coin_redis_data_client.get_coin_full_info(
            provider, from_coin, from_coin_network
        )
        to_coin_info = await coin_redis_data_client.get_coin_full_info(
            provider, to_coin, to_coin_network
        )

        if not from_coin_info or not to_coin_info:
            continue

        rate_obj = await changelly_client.get_fixed_rate(
            changelly_schemas.CreateRate(
                from_coin=from_coin_info.code,
                to_coin=to_coin_info.code
            )
        )

        if not rate_obj:
            continue

        rate = get_rate(rate_obj)

        if rate and (best_rate is None or rate > best_rate):
            best_rate = rate
            exchanger = provider.value
            best_rate_obj = rate_obj

    return [exchanger, best_rate_obj] if best_rate_obj else best_rate_obj


async def get_float_best_rate(
        from_coin: str, from_coin_network: str,
        to_coin: str, to_coin_network: str) -> list[str, RatesSchema] | None:
    best_rate = None
    best_rate_obj: RatesSchema = None
    exchanger = None

    cached_rate = await coin_redis_data_client.get_float_best_rate(
        from_coin, from_coin_network, to_coin, to_coin_network
    )
    if cached_rate:
        best_rate = get_rate(cached_rate[1])
        best_rate_obj = cached_rate[1]
        exchanger = cached_rate[0]

    providers = [Exchangers.CHANGELLY]

    for provider in providers:
        from_coin_info = await coin_redis_data_client.get_coin_full_info(
            provider, from_coin, from_coin_network
        )
        to_coin_info = await coin_redis_data_client.get_coin_full_info(
            provider, to_coin, to_coin_network
        )

        if not from_coin_info or not to_coin_info:
            continue

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

    return [exchanger, best_rate_obj] if best_rate_obj else best_rate_obj


async def get_rate_in_usdt(
        from_coin: str, from_coin_network: str) -> RatesSchema | None:
    rate = await coin_redis_data_client.get_coin_in_usdt(
        from_coin, from_coin_network)
    if rate:
        return rate[1]

    networks_usdt = await coin_redis_data_client.get_networks('USDT')
    if not networks_usdt:
        return None

    coin_info = await coin_redis_data_client.get_coin_full_info(
        Exchangers.CHANGELLY, from_coin, from_coin_network
    )
    if not coin_info:
        return None

    for net_usdt in networks_usdt:
        usdt_info = await coin_redis_data_client.get_coin_full_info(
            Exchangers.CHANGELLY, 'USDT', net_usdt
        )
        if not usdt_info:
            continue

        rate = await changelly_client.get_float_rate(
            changelly_schemas.CreateRate(
                from_coin=coin_info.code,
                to_coin=usdt_info.code
            )
        )
        if rate:
            return rate
    return None
