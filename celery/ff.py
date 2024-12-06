from celery import app

@app.task
def example_task():
    print('Task is running...')
