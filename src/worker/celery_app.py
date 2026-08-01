from celery import Celery
import os
from dotenv import load_dotenv
from api.utils.redis_utils import get_redis_url
from celery.schedules import crontab

load_dotenv()

redis_url = get_redis_url()

# Celery (Kombu) explicitly requires CERT_NONE instead of none
celery_redis_url = redis_url.replace("none", "CERT_NONE")

celery_app = Celery(
    "moveiq_worker",
    broker=celery_redis_url,
    backend=celery_redis_url,
    include=["src.worker.tasks", "src.worker.notification_tasks", "src.worker.scheduled_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# Auto-discover tasks in specific modules
celery_app.autodiscover_tasks([
    'src.worker.tasks', 
    'src.worker.notification_tasks',
    'src.worker.scheduled_tasks'
])

# Configure task routing to specific queues
celery_app.conf.task_routes = {
    'src.worker.notification_tasks.send_otp_*': {'queue': 'high_priority'},
    'src.worker.notification_tasks.send_security_alert_task': {'queue': 'high_priority'},
    'src.worker.notification_tasks.*': {'queue': 'default'},
    'src.worker.tasks.*': {'queue': 'video_processing'},
    'src.worker.scheduled_tasks.*': {'queue': 'low_priority'},
}

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    'weekly-progress-report-monday-8am': {
        'task': 'src.worker.scheduled_tasks.weekly_progress_report_task',
        'schedule': crontab(hour=8, minute=0, day_of_week=1), # Every Monday at 8 AM
    },
    'daily-reassessment-reminder-10am': {
        'task': 'src.worker.scheduled_tasks.reassessment_reminder_task',
        'schedule': crontab(hour=10, minute=0), # Every day at 10 AM
    },
    'nightly-cloudinary-cleanup-midnight': {
        'task': 'src.worker.scheduled_tasks.cleanup_cloudinary_videos_task',
        'schedule': crontab(hour=0, minute=0), # Every night at midnight
    },
}
