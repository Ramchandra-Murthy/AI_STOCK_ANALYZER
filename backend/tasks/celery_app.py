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
        celery_instance = Celery(
            "eros_enterprise",
            broker=broker_url,
            backend=result_backend,
        )
        celery_instance.conf.update(
            task_serializer="json",
            result_serializer="json",
            accept_content=["json"],
            timezone="UTC",
            enable_utc=True,
        )
        logger.info("Initialized real Enterprise Celery broker at %s", broker_url)
        
        # Automatically register all EROS application tasks upon real Celery instantiation
        try:
            from backend.tasks.task_registry import register_all_tasks
            register_all_tasks()
            logger.info("Automatically registered all enterprise tasks during Celery initialization.")
        except Exception as reg_exc:
            logger.warning("Automatic task registration during celery initialization deferred: %s", reg_exc)

    except Exception as exc:
        logger.warning("Failed to initialize real Celery broker: %s", exc)
        celery_instance = None
        USE_REAL_CELERY = False

class MockCeleryApp:
    def __init__(self, broker_url: str = "redis://localhost:6379/0") -> None:
        self.broker_url = broker_url
        self.tasks: Dict[str, Callable[..., Any]] = {
            "valuation.execute": lambda *a, **kw: {"status": "success"},
            "forecast.execute": lambda *a, **kw: {"status": "success"},
            "report.generate": lambda *a, **kw: {"status": "success"},
            "forecast.run": lambda *a, **kw: {"status": "success"},
        }

    def task(self, *args, **kwargs):
        def decorator(func):
            name = kwargs.get("name", func.__name__)
            self.tasks[name] = func
            return func
        return decorator

    def register_task(self, name: str, func: Callable[..., Any]) -> None:
        self.tasks[name] = func

    def send_task(
        self,
        name: str,
        args: tuple = (),
        kwargs: dict | None = None,
        task_id: str | None = None,
    ) -> str:
        if name not in self.tasks:
            raise ValueError(f"Unknown task: {name}")
        return f"TASK-{hash(name) % 1000000:06X}"

class CeleryFacade:
    def __init__(self, app) -> None:
        self._app = app

    @property
    def tasks(self):
        return self._app.tasks

    def task(self, *args, **kwargs):
        return self._app.task(*args, **kwargs)

    def register_task(self, name: str, func: Callable[..., Any]) -> None:
        if name not in self._app.tasks:
            self._app.task(name=name, bind=True)(func)

    def send_task(self, name: str, args: tuple = (), kwargs: dict | None = None, task_id: str | None = None) -> str:
        if name not in self._app.tasks:
            raise ValueError(f"Unknown task: {name}")
        send_kw = {"args": args, "kwargs": kwargs or {}}
        if task_id is not None:
            send_kw["task_id"] = task_id
        result = self._app.send_task(name, **send_kw)
        return str(result.id)

if USE_REAL_CELERY and celery_instance is not None:
    celery_app = CeleryFacade(celery_instance)
else:
    celery_app = MockCeleryApp()
