from celery import Celery

celery_app = Celery('tasks', broker='redis://redis:6379/0')
celery_app.conf.broker_url = 'redis://redis:6379/0'


celery_app.conf.beat_schedule = {
    'run_every_second': {
        'task': 'ff.example_task',
        'schedule': 1.0,
    },
}
celery_app.conf.timezone = 'UTC'
