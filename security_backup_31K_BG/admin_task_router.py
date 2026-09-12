from __future__ import annotations

from fastapi import APIRouter, status

from backend.infrastructure.redis.client import redis_client
from backend.tasks.celery_config import celery_broker

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Distributed Infrastructure"])


@router.get("/tasks", status_code=status.HTTP_200_OK)
def list_active_tasks() -> dict:
    return {
        "status": "SUCCESS",
        "active_tasks_count": len(celery_broker.active_tasks),
        "tasks": celery_broker.active_tasks,
    }


@router.get("/queues", status_code=status.HTTP_200_OK)
def get_queue_status() -> dict:
    return {
        "status": "SUCCESS",
        "queues": celery_broker.config.TASK_QUEUES,
        "routing": celery_broker.config.TASK_ROUTES,
    }


@router.get("/cache/stats", status_code=status.HTTP_200_OK)
def get_cache_stats() -> dict:
    return {
        "status": "SUCCESS",
        "cache_backend": "RedisClientStub",
        "stored_keys": list(redis_client._store.keys()),
    }
