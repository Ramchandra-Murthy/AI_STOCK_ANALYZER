from __future__ import annotations

import logging
import os
from typing import Dict, Any
from kombu import Queue, Exchange

logger = logging.getLogger(__name__)

class CeleryConfig:
    BROKER_URL: str = os.getenv(
        "CELERY_BROKER_URL",
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )
    RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND",
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )
    TASK_QUEUES: list = [
        Queue("valuation_queue", Exchange("valuation_exchange"), routing_key="valuation.#"),
        Queue("forecast_queue", Exchange("forecast_exchange"), routing_key="forecast.#"),
        Queue("research_queue", Exchange("research_exchange"), routing_key="research.#"),
        Queue("portfolio_queue", Exchange("portfolio_exchange"), routing_key="portfolio.#"),
        Queue("report_queue", Exchange("report_exchange"), routing_key="report.#"),
        Queue("maintenance_queue", Exchange("maintenance_exchange"), routing_key="maintenance.#"),
    ]
    TASK_ROUTES: Dict[str, str] = {
        "valuation.*": "valuation_queue",
        "forecast.*": "forecast_queue",
        "research.*": "research_queue",
        "portfolio.*": "portfolio_queue",
        "report.*": "report_queue",
        "maintenance.*": "maintenance_queue"
    }

class ProductionCeleryBroker:
    def __init__(self) -> None:
        self.config = CeleryConfig()
        self.active_tasks: dict[str, Dict[str, Any]] = {}

    def dispatch(self, task_name: str, queue: str, payload: Dict[str, Any]) -> str:
        task_id = f"CELERY-{hash(task_name + queue) % 1000000:06X}"
        self.active_tasks[task_id] = {
            "task_name": task_name,
            "queue": queue,
            "status": "QUEUED",
            "payload": payload
        }
        logger.info("Dispatched task %s to queue %s with ID %s", task_name, queue, task_id)
        return task_id

celery_broker = ProductionCeleryBroker()
