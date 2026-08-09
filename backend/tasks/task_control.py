from __future__ import annotations

import logging
import os
from typing import Any, Dict
from backend.tasks.celery_app import celery_app, celery_instance

logger = logging.getLogger(__name__)

class TaskControlService:
    """
    EROS 3.0 task control-plane facade.
    Provides a single API-facing abstraction over:
      - deterministic MockCeleryApp with task state tracking
      - real Celery + Redis execution
    """
    def __init__(self) -> None:
        self._app = celery_app
        self._real_celery = (
            os.getenv("USE_REAL_CELERY", "false").lower() == "true"
            and celery_instance is not None
        )
        # In-memory store for mock task states and results
        self._mock_tasks: Dict[str, Dict[str, Any]] = {}

    @property
    def real_celery_enabled(self) -> bool:
        return self._real_celery

    def submit_task(
        self,
        task_name: str,
        user: str,
        payload: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Submit an EROS task through the configured execution facade.
        """
        payload = payload or {}
        if not task_name:
            raise ValueError("task_name is required")
        if task_name not in self._app.tasks:
            raise ValueError(f"Unknown task: {task_name}")

        # Generate the task through the configured Celery facade.
        task_id = self._app.send_task(
            task_name,
            args=[
                "",
                task_name,
                user,
                payload,
            ],
        )

        # Record initial state in mock registry if not real celery
        self._mock_tasks[task_id] = {
            "task_id": task_id,
            "task_name": task_name,
            "user": user,
            "status": "SUCCESS" if not self._real_celery else "QUEUED",
            "result": {"status": "SUCCESS", "symbol": payload.get("symbol", "DEFAULT.NS")} if not self._real_celery else None,
        }

        logger.info(
            "Task submitted: task=%s user=%s task_id=%s real=%s",
            task_name,
            user,
            task_id,
            self._real_celery,
        )

        return {
            "task_id": task_id,
            "status": "QUEUED",
            "task_name": task_name,
            "user": user,
            "execution_result": {
                "status": "SUCCESS" if not self._real_celery else "QUEUED",
                "data": {},
            },
        }

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Return task status.
        Real Celery mode queries the Redis-backed result backend.
        Mock mode queries deterministic local memory store.
        """
        if not task_id:
            raise ValueError("task_id is required")

        if not self._real_celery or celery_instance is None:
            if task_id in self._mock_tasks:
                meta = self._mock_tasks[task_id]
                return {
                    "task_id": task_id,
                    "status": meta["status"],
                    "task_name": meta["task_name"],
                    "user": meta["user"],
                    "ready": True,
                }
            return {
                "task_id": task_id,
                "status": "NOT_FOUND",
                "ready": False,
            }

        from celery.result import AsyncResult
        result = AsyncResult(task_id, app=celery_instance)
        response: Dict[str, Any] = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
        }
        return response

    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        Return the execution result payload for a given task ID.
        """
        if not task_id:
            raise ValueError("task_id is required")

        if not self._real_celery or celery_instance is None:
            if task_id in self._mock_tasks:
                meta = self._mock_tasks[task_id]
                return {
                    "task_id": task_id,
                    "status": meta["status"],
                    "result": meta["result"],
                }
            return {
                "task_id": task_id,
                "status": "NOT_FOUND",
                "result": None,
            }

        from celery.result import AsyncResult
        result = AsyncResult(task_id, app=celery_instance)
        response: Dict[str, Any] = {
            "task_id": task_id,
            "status": result.status,
        }
        try:
            response["result"] = result.result if result.ready() else None
        except Exception as exc:
            response["result_error"] = repr(exc)
            response["result"] = None

        return response

    def get_registered_tasks(self) -> list[str]:
        """Return the task names known by the configured facade."""
        return sorted(self._app.tasks.keys())

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Return queue/control-plane information.
        """
        queues = [
            "default",
            "valuation_queue",
            "forecast_queue",
            "research_queue",
            "portfolio_queue",
            "report_queue",
            "maintenance_queue",
        ]
        workers: Dict[str, Any] = {}
        if self._real_celery and celery_instance is not None:
            try:
                inspector = celery_instance.control.inspect(timeout=2.0)
                active = inspector.active() or {}
                registered = inspector.registered() or {}
                workers = {
                    worker_name: {
                        "active_tasks": len(tasks or []),
                        "registered_tasks": len(
                            (registered or {}).get(worker_name, []) or []
                        ),
                    }
                    for worker_name, tasks in active.items()
                }
            except Exception as exc:
                logger.warning(
                    "Unable to inspect live Celery workers: %s",
                    exc,
                )

        return {
            "queues": queues,
            "active_workers": len(workers),
            "workers": workers,
            "status": "HEALTHY",
            "real_celery": self._real_celery,
        }

task_control = TaskControlService()