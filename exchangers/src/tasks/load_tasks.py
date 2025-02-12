import asyncio

from src.loaders import LoadFFIODataToRedis, LoadChangellyDataToRedis


ffio = LoadFFIODataToRedis()
changelly = LoadChangellyDataToRedis()


async def currencies_and_networks():
    # !!! Make note that all previouse data deletes in ffio loader, so in other
    # loaders just add values
    await ffio.load_currencies_and_networks()
    await changelly.load_currencies_and_networks()


def get_tasks():
    return [
        asyncio.create_task(currencies_and_networks()),
        asyncio.create_task(ffio.load_fixed_rates()),
        asyncio.create_task(ffio.load_float_rates()),

        # asyncio.create_task(changelly.load_fixed_rates()),
        # asyncio.create_task(changelly.load_float_rates())
    ]
