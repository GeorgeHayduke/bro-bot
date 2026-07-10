from celery import Celery
from backend.config import settings

celery = Celery(
    "jha_ml_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["backend.tasks"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)
