import asyncio
import decimal
import logging

from src.tasks import ffio_load_tasks

decimal.getcontext().prec = 8
decimal.getcontext().rounding = decimal.ROUND_DOWN

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    while True:
        tasks = []
        tasks.extend(ffio_load_tasks.get_tasks())

        await asyncio.gather(*tasks)
        logger.info('Finished loading')
        await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main())
