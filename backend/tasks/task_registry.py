from __future__ import annotations

import logging
from backend.tasks.celery_app import celery_instance
from backend.tasks.task_executor import (
    celery_forecast_wrapper,
    celery_valuation_wrapper,
    celery_report_wrapper,
)

logger = logging.getLogger(__name__)

def register_all_tasks() -> None:
    if celery_instance is None:
        logger.warning("Celery instance is None. Skipping task registration.")
        return

    # Register forecast.execute with auto-retry and strict time limits
    if "forecast.execute" not in celery_instance.tasks:
        celery_instance.task(
            name="forecast.execute",
            bind=True,
            autoretry_for=(Exception,),
            max_retries=3,
            retry_backoff=True,
            retry_backoff_max=60,
            retry_jitter=True,
            soft_time_limit=120,
            time_limit=150,
        )(celery_forecast_wrapper)
        logger.info("Registered task: forecast.execute with enterprise retry & timeout policy")

    # Register forecast.run alias
    if "forecast.run" not in celery_instance.tasks:
        celery_instance.task(
            name="forecast.run",
            bind=True,
            autoretry_for=(Exception,),
            max_retries=3,
            retry_backoff=True,
            soft_time_limit=120,
            time_limit=150,
        )(celery_forecast_wrapper)
        logger.info("Registered task: forecast.run")

    # Register valuation.execute
    if "valuation.execute" not in celery_instance.tasks:
        celery_instance.task(
            name="valuation.execute",
            bind=True,
            autoretry_for=(Exception,),
            max_retries=3,
            retry_backoff=True,
            retry_backoff_max=60,
            retry_jitter=True,
            soft_time_limit=120,
            time_limit=150,
        )(celery_valuation_wrapper)
        logger.info("Registered task: valuation.execute with enterprise retry & timeout policy")

    # Register report.generate
    if "report.generate" not in celery_instance.tasks:
        celery_instance.task(
            name="report.generate",
            bind=True,
            autoretry_for=(Exception,),
            max_retries=3,
            retry_backoff=True,
            retry_backoff_max=60,
            retry_jitter=True,
            soft_time_limit=180,
            time_limit=210,
        )(celery_report_wrapper)
        logger.info("Registered task: report.generate with enterprise retry & timeout policy")
