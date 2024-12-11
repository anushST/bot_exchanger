import asyncio

from src.loaders import LoadFFIODataToRedis

loader = LoadFFIODataToRedis()


def get_tasks():
    return [
        asyncio.create_task(loader.load_currencies_and_networks()),
        asyncio.create_task(loader.load_fixed_rates()),
        asyncio.create_task(loader.load_float_rates())
    ]
