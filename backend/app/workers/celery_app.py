"""
Celery application configuration.
"""

from celery import Celery
from celery.signals import setup_logging as celery_setup_logging

from app.core.config import settings
from app.core.logging import setup_logging

# Create Celery app
celery_app = Celery(
    "influencer_platform",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks",
        "app.workers.ingestion",
        "app.workers.ai_processing",
        "app.workers.ranking",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    accept_content=settings.celery_accept_content,
    result_serializer=settings.celery_result_serializer,
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    task_track_started=settings.celery_task_track_started,
    task_time_limit=settings.celery_task_time_limit,
    worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
    
    # Task routing
    task_routes={
        "app.workers.ingestion.*": {"queue": "ingestion"},
        "app.workers.ai_processing.*": {"queue": "ai_processing"},
        "app.workers.ranking.*": {"queue": "scoring"},
    },
    
    # Result backend
    result_expires=3600 * 24,  # 24 hours
    result_extended=True,
    
    # Task annotations
    task_annotations={
        "*": {
            "rate_limit": "10/s"
        }
    }
)


@celery_setup_logging.connect
def config_loggers(*args, **kwargs):
    """Configure logging for Celery workers."""
    setup_logging()


# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "sync-youtube-channels": {
        "task": "app.workers.ingestion.sync_all_youtube_channels",
        "schedule": 3600.0,  # Every hour
    },
    "sync-github-accounts": {
        "task": "app.workers.ingestion.sync_all_github_accounts",
        "schedule": 3600.0,  # Every hour
    },
    "process-pending-content": {
        "task": "app.workers.ai_processing.process_pending_content",
        "schedule": 300.0,  # Every 5 minutes
    },
    "calculate-rankings": {
        "task": "app.workers.ranking.calculate_all_rankings",
        "schedule": 86400.0,  # Every day
    },
}
