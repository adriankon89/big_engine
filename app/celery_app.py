from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "bid_engine",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)
