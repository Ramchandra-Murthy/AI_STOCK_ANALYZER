from __future__ import annotations

from backend.tasks.celery_app import celery_app
from backend.tasks.task_executor import BackgroundWorkers

def register_all_tasks() -> None:
    celery_app.register_task("valuation.execute", BackgroundWorkers.execute_valuation_task)
    celery_app.register_task("forecast.execute", BackgroundWorkers.execute_forecast_task)
    celery_app.register_task("report.generate", BackgroundWorkers.execute_report_task)

register_all_tasks()