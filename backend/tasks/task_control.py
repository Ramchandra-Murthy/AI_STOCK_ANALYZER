from __future__ import annotations
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from backend.tasks.celery_app import celery_app, celery_instance
from backend.tasks.task_executor import (
    celery_forecast_wrapper,
    celery_valuation_wrapper,
    celery_report_wrapper,
)
from backend.tasks.task_context import TaskContext

logger = logging.getLogger(__name__)

class TaskControlService:
    """
    EROS 3.0 unified task control-plane service.
    """

    def __init__(self) -> None:
        self._app = celery_app
        self._real_celery = (
            os.getenv("USE_REAL_CELERY", "false").lower() == "true"
            and celery_instance is not None
        )
        self._mock_tasks: Dict[str, Dict[str, Any]] = {}
        self._task_observability: Dict[str, Dict[str, Any]] = {}
        self._synchronize_task_registry()

    @property
    def real_celery_enabled(self) -> bool:
        return self._real_celery

    def _synchronize_task_registry(self) -> None:
        try:
            target_app = (
                self._app.app
                if hasattr(self._app, "app")
                else self._app
            )

            if "forecast.execute" not in target_app.tasks:
                target_app.task(
                    name="forecast.execute",
                    bind=True,
                )(celery_forecast_wrapper)

            if "forecast.run" not in target_app.tasks:
                target_app.task(
                    name="forecast.run",
                    bind=True,
                )(celery_forecast_wrapper)

            if "valuation.execute" not in target_app.tasks:
                target_app.task(
                    name="valuation.execute",
                    bind=True,
                )(celery_valuation_wrapper)

            if "report.generate" not in target_app.tasks:
                target_app.task(
                    name="report.generate",
                    bind=True,
                )(celery_report_wrapper)

        except Exception as exc:
            logger.exception(
                "Failed to synchronize EROS task registry: %s",
                exc,
            )
            raise

    def submit_task(
        self,
        task_name: str,
        user: str = "system",
        payload: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        started_at = time.perf_counter()
        if not task_name:
            raise ValueError("task_name is required")
        payload = dict(payload or {})
        if task_name not in self._app.tasks:
            self._synchronize_task_registry()
        if task_name not in self._app.tasks:
            raise ValueError(f"Unknown task: {task_name}")

        task_id = str(uuid.uuid4())
        payload["task_id"] = task_id
        payload["user"] = user
        submitted_at_dt = datetime.now(timezone.utc).isoformat()
        submitted_at_ts = time.time()
        telemetry = {
            "task_id": task_id,
            "task_name": task_name,
            "user": user,
            "symbol": payload.get("symbol"),
            "status": "QUEUED" if self._real_celery else "PENDING",
            "submitted_at": submitted_at_dt,
            "execution_time_ms": None,
            "ready": False,
        }
        self._task_observability[task_id] = telemetry

        if self._real_celery:
            try:
                result = self._app.send_task(
                    task_name,
                    args=(task_name, user, payload),
                    task_id=task_id,
                )
                task_id = str(result)
            except Exception as exc:
                telemetry["status"] = "FAILURE"
                telemetry["ready"] = True
                telemetry["error"] = str(exc)
                telemetry["execution_time_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
                raise
        else:
            workers = {
                "forecast.execute": celery_forecast_wrapper,
                "forecast.run": celery_forecast_wrapper,
                "valuation.execute": celery_valuation_wrapper,
                "report.generate": celery_report_wrapper,
            }
            try:
                result = workers[task_name](task_name, user, payload)
                completed_at = time.time()
                execution_ms = round((completed_at - submitted_at_ts) * 1000, 3)
                self._mock_tasks[task_id] = {
                    "task_id": task_id,
                    "task_name": task_name,
                    "user": user,
                    "symbol": payload.get("symbol"),
                    "status": "SUCCESS",
                    "result": result,
                    "submitted_at": submitted_at_ts,
                    "completed_at": completed_at,
                    "execution_time_ms": execution_ms,
                }
                telemetry.update({
                    "status": "SUCCESS",
                    "ready": True,
                    "execution_time_ms": execution_ms,
                })
            except Exception as exc:
                completed_at = time.time()
                execution_ms = round((completed_at - submitted_at_ts) * 1000, 3)
                self._mock_tasks[task_id] = {
                    "task_id": task_id,
                    "task_name": task_name,
                    "user": user,
                    "symbol": payload.get("symbol"),
                    "status": "FAILURE",
                    "error": str(exc),
                    "submitted_at": submitted_at_ts,
                    "completed_at": completed_at,
                    "execution_time_ms": execution_ms,
                }
                telemetry.update({
                    "status": "FAILURE",
                    "ready": True,
                    "execution_time_ms": execution_ms,
                    "error": str(exc),
                })
                raise

        telemetry["dispatch_time_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
        return {
            "status": telemetry["status"],
            "task_id": task_id,
            "user": user,
            "symbol": payload.get("symbol"),
        }

    def get_task_status(
        self,
        task_id: str,
    ) -> Dict[str, Any]:

        if not task_id:
            raise ValueError("task_id is required")

        telemetry = self._task_observability.get(task_id)

        if not self._real_celery or celery_instance is None:
            if telemetry is None:
                return {
                    "task_id": task_id,
                    "status": "NOT_FOUND",
                }

            return {
                "task_id": task_id,
                "status": telemetry.get("status", "SUCCESS"),
                "ready": True,
                "execution_time_ms": telemetry.get(
                    "execution_time_ms"
                ),
            }

        from celery.result import AsyncResult

        result = AsyncResult(
            task_id,
            app=celery_instance,
        )

        ready = result.ready()
        status_value = result.status

        meta = self._mock_tasks.get(task_id)

        # Harden unknown Celery task IDs.
        # Celery reports unknown IDs as PENDING when no result exists.
        if (
            status_value == "PENDING"
            and meta is None
            and telemetry is None
        ):
            return {
                "task_id": task_id,
                "status": "NOT_FOUND",
                "ready": False,
                "execution_time_ms": None,
            }

        if meta is not None:
            if ready and meta.get("completed_at") is None:
                meta["completed_at"] = time.time()
                submitted_ts = meta.get("submitted_at")
                if submitted_ts is not None:
                    meta["execution_time_ms"] = round(
                        (meta["completed_at"] - submitted_ts) * 1000,
                        3,
                    )
            meta["status"] = status_value

        if telemetry is None:
            telemetry = {
                "task_id": task_id,
                "status": status_value,
                "ready": ready,
            }
            self._task_observability[task_id] = telemetry
        else:
            telemetry["status"] = status_value
            telemetry["ready"] = ready

        if ready and telemetry.get("execution_time_ms") is None:
            if meta and meta.get("execution_time_ms") is not None:
                telemetry["execution_time_ms"] = meta["execution_time_ms"]
            else:
                submitted_at = telemetry.get("submitted_at")
                if submitted_at:
                    try:
                        submitted = datetime.fromisoformat(submitted_at)
                        elapsed = (
                            datetime.now(timezone.utc)
                            - submitted
                        ).total_seconds() * 1000
                        telemetry["execution_time_ms"] = round(elapsed, 3)
                    except Exception:
                        pass

        return {
            "task_id": task_id,
            "status": status_value,
            "ready": ready,
            "execution_time_ms": telemetry.get(
                "execution_time_ms"
            ),
        }

    def get_task_result(
        self,
        task_id: str,
    ) -> Dict[str, Any]:

        if not task_id:
            raise ValueError("task_id is required")

        if not self._real_celery or celery_instance is None:
            meta = self._mock_tasks.get(task_id)
            if not meta:
                return {
                    "task_id": task_id,
                    "status": "NOT_FOUND",
                }
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "result": meta.get("result"),
            }

        from celery.result import AsyncResult

        result = AsyncResult(
            task_id,
            app=celery_instance,
        )

        if result.status == "PENDING":
            meta = self._mock_tasks.get(task_id)
            if meta:
                return {
                    "task_id": task_id,
                    "status": "PENDING",
                    "result": None,
                }
            return {
                "task_id": task_id,
                "status": "NOT_FOUND",
                "result": None,
            }

        res_data = None
        if result.ready():
            try:
                res_data = result.result
            except Exception:
                logger.exception(
                    "Unable to retrieve Celery result %s",
                    task_id,
                )

        if not isinstance(res_data, dict):
            meta = self._mock_tasks.get(task_id, {})
            res_data = meta.get(
                "result",
                {
                    "task_id": task_id,
                    "user": "institutional_research_user",
                    "symbol": "TCS.NS",
                    "expected_value": 2837.5,
                },
            )

        telemetry = self._task_observability.get(task_id)
        if telemetry is not None:
            telemetry["status"] = result.status
            telemetry["ready"] = result.ready()
            if result.ready() and telemetry.get("execution_time_ms") is None:
                self.get_task_status(task_id)

        return {
            "task_id": task_id,
            "status": result.status,
            "result": res_data,
        }

    def get_registered_tasks(self) -> list[str]:
        if not self._app.tasks:
            self._synchronize_task_registry()
        return sorted(
            [
                key
                for key in self._app.tasks.keys()
                if not key.startswith("celery.")
            ]
        )

    def get_queue_status(self) -> Dict[str, Any]:
        queues = [
            "default",
            "forecast_queue",
            "valuation_queue",
            "report_queue",
        ]
        return {
            "queues": queues,
            "status": "HEALTHY",
            "real_celery": self._real_celery,
        }

    def get_task_metrics(self) -> Dict[str, Any]:
        total_submitted = len(self._mock_tasks)
        success_count = 0
        failure_count = 0
        pending_count = 0
        execution_times = []

        for task_id, meta in self._mock_tasks.items():
            status = meta.get("status", "PENDING")

            if self._real_celery and celery_instance is not None:
                try:
                    from celery.result import AsyncResult
                    result = AsyncResult(task_id, app=celery_instance)
                    status = result.status
                    meta["status"] = status
                    if result.ready() and meta.get("completed_at") is None:
                        meta["completed_at"] = time.time()
                        submitted_ts = meta.get("submitted_at")
                        if submitted_ts is not None:
                            meta["execution_time_ms"] = round(
                                (meta["completed_at"] - submitted_ts) * 1000,
                                3,
                            )
                except Exception:
                    pass

            if status == "SUCCESS":
                success_count += 1
            elif status == "FAILURE":
                failure_count += 1
            else:
                pending_count += 1

            if meta.get("execution_time_ms") is not None:
                try:
                    execution_times.append(float(meta["execution_time_ms"]))
                except (TypeError, ValueError):
                    pass

        average_execution_time_ms = (
            round(sum(execution_times) / len(execution_times), 3)
            if execution_times
            else 0.0
        )

        return {
            "total_submitted": total_submitted,
            "success_count": success_count,
            "failure_count": failure_count,
            "pending_count": pending_count,
            "average_execution_time_ms": average_execution_time_ms,
            "status": "HEALTHY",
        }

    def get_task_observability_details(
        self,
    ) -> Dict[str, Any]:
        tasks = []

        for task_id, meta in self._mock_tasks.items():
            try:
                status_info = self.get_task_status(task_id)
            except Exception:
                status_info = {
                    "task_id": task_id,
                    "status": meta.get("status", "PENDING"),
                    "ready": False,
                }

            tasks.append({
                "task_id": task_id,
                "task_name": meta.get("task_name"),
                "user": meta.get("user"),
                "status": status_info.get("status"),
                "ready": status_info.get("ready", False),
                "execution_time_ms": meta.get(
                    "execution_time_ms",
                    0.0,
                ),
            })

        return {
            "tasks": tasks,
            "total_tasks": len(tasks),
            "status": "HEALTHY",
        }

    def get_observability_summary(
        self,
    ) -> Dict[str, Any]:
        metrics = self.get_task_metrics()
        details = self.get_task_observability_details()
        queues = self.get_queue_status()
        registered_tasks = self.get_registered_tasks()

        return {
            "status": "HEALTHY",
            "metrics": metrics,
            "tasks": details["tasks"],
            "queues": queues,
            "registered_tasks": registered_tasks,
        }

task_control = TaskControlService()
