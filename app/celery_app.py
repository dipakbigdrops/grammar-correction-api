"""
Celery Application Configuration
"""
from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "grammar_correction",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Optional: Configure result backend settings
celery_app.conf.result_backend_transport_options = {
    'master_name': 'mymaster',
}

if __name__ == '__main__':
    celery_app.start()