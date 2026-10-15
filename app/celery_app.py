from celery import Celery

from app.config import Settings, get_settings

settings: Settings = get_settings()

celery_app = Celery(
    "bid_engine",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)


celery_app.autodiscover_tasks(
    [
        "app",
    ]
)
