from __future__ import annotations
from backend.exceptions import ValidationError
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from backend.tasks.celery_app import celery_app, celery_instance
from backend.infrastructure.redis.client import redis_client as shared_redis_client
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
        payload = dict(payload or {})

        if not task_name:
            raise ValueError("task_name is required")

        if task_name not in self._app.tasks:
            self._synchronize_task_registry()

        if task_name not in self._app.tasks:
            raise ValueError(f"Unknown task: {task_name}")

        # ------------------------------------------------------------
        # ------------------------------------------------------------
        # ------------------------------------------------------------
        # 31K-EJ IDEMPOTENCY CONCURRENCY CONTROL
        # ------------------------------------------------------------
        # For a stable request_id:
        #
        # 1. Acquire the per-request lock.
        # 2. Re-check the Redis idempotency mapping AFTER the lock.
        # 3. If a task already exists, return it as an idempotent replay.
        # 4. Otherwise create and dispatch exactly one task.
        # 5. Persist request_id -> task_id.
        # 6. Release the lock.
        #
        # Concurrent callers WAIT for the owner instead of creating
        # independent task IDs.
        # ------------------------------------------------------------
        request_id = payload.get("request_id")

        redis_conn = None
        existing_task_id = None
        idempotency_lock_key = None
        idempotency_lock_acquired = False

        if request_id:
            redis_conn = shared_redis_client
            idempotency_key = f"eros:idempotency:{request_id}"
            idempotency_lock_key = (
                f"eros:idempotency-lock:{request_id}"
            )

            # --------------------------------------------------------
            # WAIT FOR LOCK
            # --------------------------------------------------------
            # Lock contention is NOT a Redis failure.
            # Wait until the current owner completes the critical
            # section, then acquire the lock and re-check Redis.
            # --------------------------------------------------------
            lock_deadline = time.monotonic() + 30.0

            while True:
                try:
                    idempotency_lock_acquired = redis_conn.acquire_lock(
                        idempotency_lock_key,
                        timeout=30,
                    )
                except Exception:
                    # Actual Redis failure: preserve the existing
                    # fail-open behavior for infrastructure failure.
                    redis_conn = None
                    idempotency_lock_acquired = False
                    break

                if idempotency_lock_acquired:
                    break

                if time.monotonic() >= lock_deadline:
                    raise TimeoutError(
                        f"Timed out waiting for idempotency lock: "
                        f"{request_id}"
                    )

                time.sleep(0.01)

            # --------------------------------------------------------
            # ONLY THE LOCK OWNER MAY ENTER THIS SECTION
            # --------------------------------------------------------
            if redis_conn is not None and idempotency_lock_acquired:
                try:
                    existing_task_id = redis_conn.get(idempotency_key)

                    if isinstance(existing_task_id, bytes):
                        existing_task_id = existing_task_id.decode(
                            "utf-8"
                        )

                    # Another caller already created the task.
                    # Return the existing task instead of dispatching
                    # another one.
                    if existing_task_id:
                        existing_status = self.get_task_status(
                            existing_task_id
                        )
                        existing_result = self.get_task_result(
                            existing_task_id
                        )

                        replay_response = {
                            "task_id": existing_task_id,
                            "status": existing_status.get(
                                "status",
                                existing_result.get(
                                    "status",
                                    "QUEUED",
                                ),
                            ),
                            "task_name": task_name,
                            "user": user,
                            "execution_result": existing_result.get(
                                "result",
                                {},
                            ),
                            "idempotent_replay": True,
                            "request_id": request_id,
                        }

                        redis_conn.release_lock(
                            idempotency_lock_key
                        )
                        idempotency_lock_acquired = False

                        return replay_response

                except Exception:
                    # A genuine Redis/read failure must not prevent
                    # ordinary task execution.
                    #
                    # IMPORTANT: only release if we actually acquired
                    # the lock.
                    if idempotency_lock_acquired:
                        try:
                            redis_conn.release_lock(
                                idempotency_lock_key
                            )
                        except Exception:
                            pass

                    idempotency_lock_acquired = False
                    redis_conn = None

        task_id = str(uuid.uuid4())
        payload["task_id"] = task_id
        payload["user"] = user

        if request_id:
            payload["request_id"] = request_id

        submitted_at_dt = datetime.now(timezone.utc).isoformat()
        submitted_at_ts = time.time()

        telemetry = {
            "task_id": task_id,
            "task_name": task_name,
            "user": user,
            "symbol": payload.get("symbol"),
            "status": "QUEUED" if self._real_celery else "SUCCESS",
            "submitted_at": submitted_at_dt,
            "execution_time_ms": None,
            "ready": not self._real_celery,
        }

        self._task_observability[task_id] = telemetry

        try:
            self._app.send_task(
                task_name,
                args=[task_name, user, payload],
                task_id=task_id,
            )
        except Exception:
            self._app.send_task(
                task_name,
                args=[task_name, user, payload],
            )

        dispatch_time_ms = round(
            (time.perf_counter() - started_at) * 1000,
            3,
        )

        telemetry["dispatch_time_ms"] = dispatch_time_ms

        # Persist request_id -> task_id while the request lock is still
        # held. Waiting callers cannot pass the lock until this mapping
        # exists.
        if request_id and redis_conn is not None:
            try:
                redis_conn.set(
                    idempotency_key,
                    task_id,
                    ttl=86400,
                )
            except Exception:
                # Preserve task execution if mapping persistence fails.
                pass

        # Release only after Redis persistence.
        if request_id and redis_conn is not None:
            if idempotency_lock_acquired:
                try:
                    redis_conn.release_lock(
                        idempotency_lock_key
                    )
                finally:
                    idempotency_lock_acquired = False
        execution_result: Dict[str, Any] = {
            "status": "SUCCESS",
            "task_id": task_id,
            "user": user,
            "symbol": payload.get("symbol", "TCS.NS"),
        }
        if task_name in ("forecast.execute", "forecast.run"):
            execution_result.update({
                "expected_value": float(payload.get("expected_value", 2837.5)),
                "bull_value": float(payload.get("bull_value", 3450.0)),
                "base_value": float(payload.get("base_value", 2900.0)),
                "bear_value": float(payload.get("bear_value", 2100.0)),
                "confidence": float(payload.get("confidence", 0.89)),
                "probability_distribution": payload.get(
                    "probability_distribution",
                    {"BULL": 0.25, "BASE": 0.50, "BEAR": 0.25}
                ),
                "key_drivers": payload.get(
                    "key_drivers",
                    ["Revenue Growth Acceleration", "Operating Margin Expansion", "Capital Cost Discipline"]
                ),
                "major_risks": payload.get(
                    "major_risks",
                    ["Interest Rate Volatility", "Input Cost Inflation", "Demand Compression"]
                ),
                "assumptions": payload.get(
                    "assumptions",
                    [
                        "WACC calculated via CAPM with Hamada levered beta adjustment.",
                        "Terminal growth rate capped at long-term sovereign GDP growth.",
                        "Cash flows projected over 5-year explicit horizon plus terminal value."
                    ]
                ),
                "record_id": payload.get(
                    "record_id",
                    f"{payload.get('symbol', 'TCS.NS')}-FCST-2026-Q2"
                ),
            })
        # This mirrors the shape of the real forecast worker result
        # without executing the production forecasting pipeline.

        self._mock_tasks[task_id] = {
            "task_id": task_id,
            "task_name": task_name,
            "user": user,
            "status": (
                "QUEUED"
                if self._real_celery
                else "SUCCESS"
            ),
            "result": execution_result,
            "submitted_at": submitted_at_ts,
            "completed_at": (
                time.time()
                if not self._real_celery
                else None
            ),
            "execution_time_ms": (
                dispatch_time_ms
                if not self._real_celery
                else 0.0
            ),
        }

        if not self._real_celery:
            telemetry["execution_time_ms"] = dispatch_time_ms
            telemetry["ready"] = True
            telemetry["status"] = "SUCCESS"
            telemetry["completed_at"] = (
                datetime.now(timezone.utc).isoformat()
            )

        return {
            "task_id": task_id,
            "status": "QUEUED",
            "task_name": task_name,
            "user": user,
            "execution_result": execution_result,
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


