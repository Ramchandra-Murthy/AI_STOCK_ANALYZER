from __future__ import annotations

from datetime import UTC, datetime

from api.schemas import ApiResponse
from services.workflow.orchestration import InstitutionalResearchPipeline


def run_workflow(symbol: str) -> ApiResponse:
    """Execute the institutional research lifecycle and normalize its response."""
    result = InstitutionalResearchPipeline.execute_full_research_lifecycle(symbol)
    return ApiResponse(
        success=len(result.failed_steps) == 0,
        version="1.0.0",
        timestamp=datetime.now(UTC).isoformat(),
        data={
            "run_id": result.run_id,
            "completed_steps": result.completed_steps,
            "failed_steps": result.failed_steps,
            "reports_generated": result.reports_generated,
            "execution_time": result.execution_time,
        },
        errors=result.warnings,
        metadata=result.metadata,
    )
