import asyncio
import logging
import logging.handlers
import os

from src.tasks import load_tasks

if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s|%(name)s|%(levelname)s|%(message)s|',
    handlers=[
        logging.handlers.RotatingFileHandler(
            'logs/currenciess.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def run_task(task, task_id):
    try:
        await task
    except Exception as e:
        logger.error(f'Task {task_id} failed with error: {e}', exc_info=True)


async def main():
    while True:
        try:
            tasks = load_tasks.get_tasks()

            if not tasks:
                logger.info('No tasks to execute.')
            else:
                await asyncio.gather(
                    *(run_task(task, idx) for idx, task in enumerate(
                        tasks, start=1))
                )

            logger.info('Finished loading tasks.')
        except Exception as e:
            logger.error(f'Unexpected error in main loop: {e}', exc_info=True)

        await asyncio.sleep(10)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Program stopped manually.')
    except Exception as e:
        logger.critical(f'Critical error: {e}', exc_info=True)
