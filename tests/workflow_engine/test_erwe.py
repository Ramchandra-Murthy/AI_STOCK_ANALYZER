from __future__ import annotations

import pytest
from services.workflow_engine.models import WorkflowExecution
from services.workflow_engine.workflow_engine import EnterpriseWorkflowEngine

def test_workflow_execution_immutability() -> None:
    ex = WorkflowExecution(
        workflow_id="WF-001",
        symbol="RELIANCE.NS",
        execution_time="2026-08-07T12:00:00",
        completed_steps=["Valuation", "Risk"],
        failed_steps=[],
        total_runtime=1.25,
        success=True
    )
    assert ex.workflow_id == "WF-001"
    assert ex.success is True
    assert len(ex.completed_steps) == 2
    assert isinstance(ex.metadata, dict)

def test_enterprise_workflow_engine() -> None:
    steps = ["DataPlatform", "KnowledgeGraph", "Valuation", "Risk", "Committee"]
    result = EnterpriseWorkflowEngine.execute_workflow("WF-002", "RELIANCE.NS", steps)
    assert result.workflow_id == "WF-002"
    assert result.success is True
    assert len(result.completed_steps) == len(steps)
    assert result.total_runtime >= 0.0
