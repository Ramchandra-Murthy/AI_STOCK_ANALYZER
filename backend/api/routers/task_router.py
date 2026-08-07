from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import Dict, Any
from backend.tasks.celery_app import celery_app
from backend.tasks.task_context import TaskContext
from backend.tasks.task_executor import BackgroundWorkers

router = APIRouter(prefix="/api/v1/tasks", tags=["Distributed Tasks"])

class TaskSubmitRequest(BaseModel):
    task_name: str
    user: str = "analyst1"
    payload: Dict[str, Any] = {}

@router.post("/submit", status_code=status.HTTP_202_ACCEPTED)
def submit_task(request: TaskSubmitRequest) -> dict:
    task_id = celery_app.send_task(request.task_name, kwargs={"context": TaskContext(task_id="PENDING", task_name=request.task_name, user=request.user, payload=request.payload)})
    
    # Execute immediately in background test mode or dispatch
    context = TaskContext(task_id=task_id, task_name=request.task_name, user=request.user, payload=request.payload)
    if request.task_name == "valuation.execute":
        res = BackgroundWorkers.execute_valuation_task(context)
    elif request.task_name == "forecast.execute":
        res = BackgroundWorkers.execute_forecast_task(context)
    else:
        res = BackgroundWorkers.execute_report_task(context)

    return {
        "task_id": task_id,
        "status": "QUEUED",
        "message": f"Task '{request.task_name}' accepted for asynchronous execution.",
        "execution_result": res
    }