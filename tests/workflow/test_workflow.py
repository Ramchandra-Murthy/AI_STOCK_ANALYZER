from __future__ import annotations

import pytest
from services.workflow.models import WorkflowResult
from services.workflow.orchestration import InstitutionalResearchPipeline

def test_institutional_research_pipeline() -> None:
    result = InstitutionalResearchPipeline.execute_full_research_lifecycle("RELIANCE.NS")
    
    assert result.run_id.startswith("RUN-")
    assert len(result.completed_steps) == 12
    assert len(result.failed_steps) == 0
    assert len(result.reports_generated) == 1
    assert "RELIANCE.NS" in result.reports_generated[0]
    assert result.execution_time >= 0.0
    assert result.metadata["symbol"] == "RELIANCE.NS"
    assert "Archive Results" in result.completed_steps
