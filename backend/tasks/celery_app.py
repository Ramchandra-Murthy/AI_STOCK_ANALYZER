from __future__ import annotations

import logging
import os
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)

USE_REAL_CELERY = os.getenv("USE_REAL_CELERY", "false").lower() == "true"

celery_instance = None
if USE_REAL_CELERY:
    try:
        from celery import Celery
        broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
        result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
        
        celery_instance = Celery("eros_enterprise", broker=broker_url, backend=result_backend)
        celery_instance.conf.update(
            task_serializer="json",
            result_serializer="json",
            accept_content=["json"],
            timezone="UTC",
            enable_utc=True,
        )
        logger.info("Initialized real Enterprise Celery broker at %s", broker_url)
    except Exception as e:
        logger.warning("Failed to initialize real Celery broker, falling back to MockCeleryApp: %s", e)
        USE_REAL_CELERY = False

class MockCeleryApp:
    """Enterprise mock Celery application for deterministic testing and local execution."""
    def __init__(self, broker_url: str = "redis://localhost:6379/0") -> None:
        self.broker_url = broker_url
        self.tasks: Dict[str, Callable[..., Any]] = {
            "valuation.execute": lambda *a, **kw: {"status": "success"},
            "forecast.execute": lambda *a, **kw: {"status": "success"},
            "report.generate": lambda *a, **kw: {"status": "success"},
        }

    def register_task(self, name: str, func: Callable[..., Any]) -> None:
        self.tasks[name] = func
        logger.info("Registered asynchronous background task: %s", name)

    def send_task(self, name: str, args: tuple = (), kwargs: dict = None) -> str:
        if name not in self.tasks:
            self.tasks[name] = lambda *a, **kw: {"status": "success"}
        
        task_id = f"TASK-{hash(name) % 1000000:06X}"
        logger.info("Queued task %s with ID %s", name, task_id)
        return task_id

class CeleryFacade:
    def __init__(self, app: Celery) -> None:
        self._app = app
        self.tasks: Dict[str, Callable[..., Any]] = {
            "valuation.execute": lambda *a, **kw: {"status": "success"},
            "forecast.execute": lambda *a, **kw: {"status": "success"},
            "report.generate": lambda *a, **kw: {"status": "success"},
        }

    def register_task(self, name: str, func: Callable[..., Any]) -> None:
        self.tasks[name] = func
        self._app.task(name=name, bind=True)(func)
        logger.info("Registered real Celery task: %s", name)

    def send_task(self, name: str, args: tuple = (), kwargs: dict = None) -> str:
        res = self._app.send_task(name, args=args, kwargs=kwargs or {})
        return str(res.id)

if USE_REAL_CELERY and celery_instance:
    celery_app = CeleryFacade(celery_instance)
else:
    celery_app = MockCeleryApp()