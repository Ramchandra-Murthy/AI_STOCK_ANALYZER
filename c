[1mdiff --git a/backend/api/routers/valuation_router.py b/backend/api/routers/valuation_router.py[m
[1mindex deab0cb..c18c4ed 100644[m
[1m--- a/backend/api/routers/valuation_router.py[m
[1m+++ b/backend/api/routers/valuation_router.py[m
[36m@@ -1,40 +1,2 @@[m
[31m-from __future__ import annotations[m
[31m-[m
[31m-from fastapi import APIRouter, Depends[m
[31m-from sqlalchemy.orm import Session[m
[31m-from datetime import datetime[m
[31m-from backend.api.dependencies.database import get_session[m
[31m-from backend.api.schemas.valuation import ValuationRequest, ValuationResponse[m
[31m-from backend.services.valuation_service import ValuationService[m
[31m-[m
[31m-router = APIRouter(prefix="/api/v1", tags=["Valuation"])[m
[31m-[m
[31m-@router.post("/valuation", response_model=ValuationResponse)[m
[31m-def execute_valuation(payload: ValuationRequest, session: Session = Depends(get_session)) -> ValuationResponse:[m
[31m-    metrics = {[m
[31m-        "eps": payload.eps,[m
[31m-        "growth_rate": payload.growth_rate,[m
[31m-        "discount_rate": payload.discount_rate,[m
[31m-        "current_price": payload.current_price[m
[31m-    }[m
[31m-    result = ValuationService.execute_and_persist_valuation([m
[31m-        session=session,[m
[31m-        symbol=payload.symbol,[m
[31m-        financial_metrics=metrics[m
[31m-    )[m
[31m-    [m
[31m-    iv = result["intrinsic_value"][m
[31m-    cp = result["current_price"][m
[31m-    mos = result["margin_of_safety"][m
[31m-    rec = "BUY" if mos > 0.15 else "HOLD"[m
[31m-[m
[31m-    return ValuationResponse([m
[31m-        record_id=result["record_id"],[m
[31m-        symbol=result["symbol"],[m
[31m-        intrinsic_value=iv,[m
[31m-        current_price=cp,[m
[31m-        margin_of_safety=mos,[m
[31m-        recommendation=rec,[m
[31m-        valuation_model=result["model_type"],[m
[31m-        created_at=datetime.utcnow()[m
[31m-    )[m
\ No newline at end of file[m
[32m+[m[32mfrom __future__ import annotations  from fastapi import APIRouter[m
[32m+[m[32mfrom fastapi import Depends from sqlalchemy.orm import Session from datetime import datetime from backend.api.dependencies.database import get_session from backend.api.schemas.valuation import ValuationRequest, ValuationResponse from backend.services.valuation_service import ValuationService  router = APIRouter(prefix="/api/v1", tags=["Valuation"])  @router.post("/valuation", response_model=ValuationResponse) def execute_valuation(payload: ValuationRequest, session: Session = Depends(get_session)) -> ValuationResponse:     metrics = {         "eps": payload.eps,         "growth_rate": payload.growth_rate,         "discount_rate": payload.discount_rate,         "current_price": payload.current_price     }     result = ValuationService.execute_and_persist_valuation(         session=session,         symbol=payload.symbol,         financial_metrics=metrics     )          iv = result["intrinsic_value"]     cp = result["current_price"]     mos = result["margin_of_safety"]     rec = "BUY" if mos > 0.15 else "HOLD"      return ValuationResponse(         record_id=result["record_id"],         symbol=result["symbol"],         intrinsic_value=iv,         current_price=cp,         margin_of_safety=mos,         recommendation=rec,         valuation_model=result["model_type"],         created_at=datetime.utcnow()     )[m
\ No newline at end of file[m
