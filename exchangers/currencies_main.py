import asyncio
import logging

from src.tasks import ffio_load_tasks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def run_task(task, task_id):
    try:
        logger.info(f'Starting task {task_id}')
        await task
        logger.info(f'Task {task_id} completed successfully')
    except Exception as e:
        logger.error(f'Task {task_id} failed with error: {e}', exc_info=True)


async def main():
    while True:
        try:
            tasks = ffio_load_tasks.get_tasks()

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
