from __future__ import annotations

from fastapi import APIRouterDepends, Depends
from backend.api.dependencies.auth import get_current_user
from sqlalchemy.orm import Session
from datetime import datetime
from backend.api.dependencies.database import get_session
from backend.api.schemas.valuation import ValuationRequest, ValuationResponse
from backend.services.valuation_service import ValuationService

router = APIRouter(prefix="/api/v1", tags=["Valuation"])

@router.post("/valuation", response_model=ValuationResponse, dependencies=[Depends(get_current_user)])
def execute_valuation(payload: ValuationRequest, session: Session = Depends(get_session)) -> ValuationResponse:
    metrics = {
        "eps": payload.eps,
        "growth_rate": payload.growth_rate,
        "discount_rate": payload.discount_rate,
        "current_price": payload.current_price
    }
    result = ValuationService.execute_and_persist_valuation(
        session=session,
        symbol=payload.symbol,
        financial_metrics=metrics
    )
    
    iv = result["intrinsic_value"]
    cp = result["current_price"]
    mos = result["margin_of_safety"]
    rec = "BUY" if mos > 0.15 else "HOLD"

    return ValuationResponse(
        record_id=result["record_id"],
        symbol=result["symbol"],
        intrinsic_value=iv,
        current_price=cp,
        margin_of_safety=mos,
        recommendation=rec,
        valuation_model=result["model_type"],
        created_at=datetime.utcnow()
    )

