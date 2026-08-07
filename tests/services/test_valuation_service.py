from __future__ import annotations

import pytest
from backend.database.engine import init_db, SessionLocal
from backend.services.valuation_service import ValuationService
from backend.database.repositories.company_repository import ValuationRepository

def test_valuation_service_orchestration() -> None:
    init_db()
    session = SessionLocal()
    try:
        metrics = {
            "eps": 85.50,
            "growth_rate": 0.08,
            "discount_rate": 0.11,
            "current_price": 2400.0
        }
        
        result = ValuationService.execute_and_persist_valuation(
            session=session,
            symbol="TCS.NS",
            financial_metrics=metrics
        )
        
        assert result["symbol"] == "TCS.NS"
        assert result["status"] == "SUCCESS"
        assert result["intrinsic_value"] > 0

        # Verify persistence via repository
        saved_record = ValuationRepository.get_valuation(session, result["record_id"])
        assert saved_record is not None
        assert saved_record.symbol == "TCS.NS"
    finally:
        session.close()