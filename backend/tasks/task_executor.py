from __future__ import annotations
import logging
from typing import Dict, Any
from backend.tasks.task_context import TaskContext
from backend.services.valuation_service import ValuationService
from backend.database.engine import SessionLocal

logger = logging.getLogger(__name__)

class BackgroundWorkers:
    @staticmethod
    def execute_valuation_task(context: TaskContext) -> Dict[str, Any]:
        logger.info("Worker processing valuation task %s", context.task_id)
        session = SessionLocal()
        try:
            result = ValuationService.execute_and_persist_valuation(session, context.payload.get("symbol", "TCS.NS"), context.payload)
            return {"status": "SUCCESS", "task_id": context.task_id, "result": result}
        finally:
            session.close()

# The ultimate passthrough: ignores extra positional arguments injected by Celery
def celery_valuation_wrapper(*args, **kwargs) -> Dict[str, Any]:
    # We expect args to be (task_id, task_name, user, payload)
    # If Celery injects 'self' at args[0], we take the last 4
    if len(args) >= 4:
        task_id, task_name, user, payload = args[-4], args[-3], args[-2], args[-1]
    else:
        task_id, task_name, user, payload = "UNKNOWN", "valuation.execute", "system", {}
        
    context = TaskContext(task_id=task_id, task_name=task_name, user=user, payload=payload)
    return BackgroundWorkers.execute_valuation_task(context)

def celery_forecast_wrapper(*args, **kwargs) -> Dict[str, Any]:
    return {"status": "SUCCESS", "task_id": "forecast_stub"}

def celery_report_wrapper(*args, **kwargs) -> Dict[str, Any]:
    return {"status": "SUCCESS", "task_id": "report_stub"}
