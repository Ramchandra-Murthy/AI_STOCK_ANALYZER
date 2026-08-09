from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any
from backend.tasks.task_control import task_control

router = APIRouter(prefix="/api/v1/tasks", tags=["Distributed Tasks"])

class TaskSubmitRequest(BaseModel):
    task_name: str
    user: str = "analyst1"
    payload: Dict[str, Any] = {}

@router.post("/submit", status_code=status.HTTP_202_ACCEPTED)
def submit_task(request: TaskSubmitRequest) -> dict:
    """
    Submit an EROS task through the unified TaskControlService facade.
    """
    submission = task_control.submit_task(
        task_name=request.task_name,
        user=request.user,
        payload=request.payload
    )

    return {
        "task_id": submission["task_id"],
        "status": submission["status"],
        "message": f"Task '{request.task_name}' accepted for asynchronous execution.",
        "execution_result": submission.get("execution_result", {})
    }
