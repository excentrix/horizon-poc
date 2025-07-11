# backend/src/background/celery_app.py
from celery import Celery
import os
from datetime import timedelta, datetime

# Create Celery instance
celery_app = Celery(
    "horizon_mentor",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
    include=[
        "background.tasks.session_analysis",
        "background.tasks.fact_extraction", 
        "background.tasks.memory_consolidation"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression="gzip",
    result_compression="gzip",
    
    # Periodic tasks
    beat_schedule={
        "memory-consolidation": {
            "task": "background.tasks.memory_consolidation.consolidate_user_memories",
            "schedule": timedelta(hours=6),  # Every 6 hours
        },
        "cleanup-old-processing-jobs": {
            "task": "background.tasks.maintenance.cleanup_old_jobs",
            "schedule": timedelta(days=1),  # Daily cleanup
        },
    },
)

# Health check task
@celery_app.task(bind=True)
def health_check(self):
    """Simple health check task."""
    return {
        "status": "healthy",
        "task_id": self.request.id,
        "timestamp": str(datetime.now())
    }

if __name__ == "__main__":
    celery_app.start()