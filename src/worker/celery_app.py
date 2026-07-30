from celery import Celery
import os
from dotenv import load_dotenv
from api.utils.redis_utils import get_redis_url

load_dotenv()

redis_url = get_redis_url()

celery_app = Celery(
    "moveiq_worker",
    broker=redis_url,
    backend=redis_url,
    include=["src.worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True
)
