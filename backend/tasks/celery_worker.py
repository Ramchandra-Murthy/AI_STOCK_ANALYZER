from __future__ import annotations
import logging
from backend.tasks.celery_app import celery_instance

if celery_instance is None:
    raise RuntimeError(
        "Real Celery is not initialized. "
        "Set USE_REAL_CELERY=true before starting the worker."
    )

from backend.tasks.task_registry import register_all_tasks
logger = logging.getLogger(__name__)

# Register all EROS application tasks AFTER Celery has been created.
register_all_tasks()

logger.info(
    "EROS Celery worker application initialized with %d tasks",
    len(
        [
            name
            for name in celery_instance.tasks
            if not name.startswith("celery.")
        ]
    ),
)

app = celery_instance
