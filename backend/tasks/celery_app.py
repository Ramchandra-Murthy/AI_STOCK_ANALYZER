from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MockCeleryApp:
    """Enterprise mock Celery application for distributed task routing and worker coordination."""
    def __init__(self, broker_url: str = "redis://localhost:6379/0") -> None:
        self.broker_url = broker_url
        self.tasks: Dict[str, Any] = {}

    def register_task(self, name: str, func: Any) -> None:
        self.tasks[name] = func
        logger.info("Registered asynchronous background task: %s", name)

    def send_task(self, name: str, args: tuple = (), kwargs: dict = None) -> str:
        if name not in self.tasks:
            raise KeyError(f"Task '{name}' is not registered with the Celery worker pool.")
        task_id = f"TASK-{hash(name) % 1000000:06X}"
        logger.info("Queued task %s with ID %s", name, task_id)
        return task_id

celery_app = MockCeleryApp()