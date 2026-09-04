from __future__ import annotations
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from services.workflow.production_orchestrator import EROSProductionWorkflowOrchestrator

router = APIRouter(prefix="/api/v1/eros", tags=["EROS 3.0 Production Workflow"])

class AnalysisRequest(BaseModel):
    symbol: str
    policy_profile: str = "Institutional"

@router.post("/evaluate", status_code=status.HTTP_200_OK)
def evaluate_stock_endpoint(request: AnalysisRequest):
    try:
        orchestrator = EROSProductionWorkflowOrchestrator(policy_profile=request.policy_profile)
        output = orchestrator.execute_workflow(request.symbol)
        return {"success": True, "data": output}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
