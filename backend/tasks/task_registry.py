from __future__ import annotations

from backend.tasks.celery_app import celery_app
from backend.tasks.task_executor import (
    BackgroundWorkers,
    celery_valuation_wrapper,
    celery_forecast_wrapper,
    celery_report_wrapper
)

def register_all_tasks() -> None:
    celery_app.register_task("valuation.execute", celery_valuation_wrapper)
    celery_app.register_task("forecast.execute", celery_forecast_wrapper)
    celery_app.register_task("report.generate", celery_report_wrapper)
    # Register aliases for backwards compatibility
    celery_app.register_task("forecast.run", celery_forecast_wrapper)

# Auto-register on module import
register_all_tasks()