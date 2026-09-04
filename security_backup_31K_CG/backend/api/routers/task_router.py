from __future__ import annotations

from fastapi import Depends

from backend.api.dependencies.auth import get_current_user
from pydantic import BaseModel
from typing import Dict, Any
from backend.tasks.task_control import task_control

router = APIRouter(prefix="/api/v1/tasks", tags=["Distributed Tasks"])

class TaskSubmitRequest(BaseModel):
    task_name: str
    user: str = "analyst1"
    payload: Dict[str, Any] = {}

@router.post("/submit", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(get_current_user)])
def submit_task(request: TaskSubmitRequest) -> dict:
    """
    Submit an EROS task through the unified TaskControlService facade.
    """
    try:
        submission = task_control.submit_task(
            task_name=request.task_name,
            user=request.user,
            payload=request.payload
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return {
        "task_id": submission["task_id"],
        "status": submission["status"],
        "message": f"Task '{request.task_name}' accepted for asynchronous execution.",
        "execution_result": submission.get("execution_result", {})
    }

@router.get("/registered", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
def get_registered_tasks() -> dict:
    """
    Return all registered task names known by the control plane.
    """
    return {"registered_tasks": task_control.get_registered_tasks()}

@router.get("/queues/status", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
def get_queue_status() -> dict:
    """
    Retrieve active queues and worker status from the control plane.
    """
    return task_control.get_queue_status()

@router.get("/{task_id}/status", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
def get_task_status(task_id: str) -> dict:
    """
    Retrieve the execution status of a given task ID.
    """
    status_info = task_control.get_task_status(task_id)
    if status_info.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return status_info

@router.get("/{task_id}/result", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
def get_task_result(task_id: str) -> dict:
    """
    Retrieve the execution result payload of a given task ID.
    """
    result_info = task_control.get_task_result(task_id)
    if result_info.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return result_info

@router.get("/observability/metrics", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
def get_task_observability_metrics() -> dict:
    """
    Retrieve enterprise task execution and lifecycle observability metrics.
    """
    metrics = task_control.get_task_metrics()
    return {
        "status": "SUCCESS",
        "metrics": metrics
    }

@router.get("/observability/details", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
def get_task_observability_details() -> dict:
    """
    Retrieve detailed per-task execution telemetry.
    """
    details = task_control.get_task_observability_details()
    return {
        "status": "SUCCESS",
        "tasks": details["tasks"],
        "total_tasks": details["total_tasks"],
    }

@router.get("/observability", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
def get_task_observability_summary() -> dict:
    """
    Retrieve comprehensive unified task control-plane observability summary.
    """
    summary = task_control.get_observability_summary()
    return {
        "status": "SUCCESS",
        "summary": summary
    }

