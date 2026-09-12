from __future__ import annotations

import pytest

from backend.workflow.workflow_context import WorkflowContext
from backend.workflow.workflow_engine import WorkflowEngine
from backend.workflow.workflow_exceptions import InvalidStateTransitionError, StageExecutionError
from backend.workflow.workflow_state import WorkflowState


def test_workflow_successful_execution() -> None:
    engine = WorkflowEngine(workflow_id="WF-001", symbol="TCS.NS", user="analyst1")

    def sample_stage(ctx: WorkflowContext) -> dict:
        return {"valuation": 3200.0, "recommendation": "BUY"}

    engine.add_stage(sample_stage)
    result_context = engine.execute()

    assert engine.state == WorkflowState.COMPLETED
    assert result_context.shared_data["valuation"] == 3200.0
    assert result_context.metrics["total_duration_ms"] > 0


def test_workflow_invalid_state_transition() -> None:
    engine = WorkflowEngine(workflow_id="WF-002", symbol="INFY.NS", user="analyst1")
    with pytest.raises(InvalidStateTransitionError):
        engine.transition_to(
            WorkflowState.COMPLETED
        )  # Cannot jump directly from CREATED to COMPLETED


def test_workflow_retry_and_failure() -> None:
    engine = WorkflowEngine(workflow_id="WF-003", symbol="RELIANCE.NS", user="admin")

    attempts = 0

    def failing_stage(ctx: WorkflowContext) -> dict:
        nonlocal attempts
        attempts += 1
        raise RuntimeError("Transient network failure")

    engine.add_stage(failing_stage)
    with pytest.raises(StageExecutionError):
        engine.execute()

    assert engine.state == WorkflowState.FAILED
    assert attempts == 3  # Initial attempt + 2 retries
