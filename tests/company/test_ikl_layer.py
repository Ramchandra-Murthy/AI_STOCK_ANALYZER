from __future__ import annotations

from services.company.predictions import PredictionLedger, PredictionRecord
from services.company.timeline import CompanyTimelineEngine, CorporateEvent


def test_company_timeline_and_predictions() -> None:
    # Test Timeline Engine
    timeline_engine = CompanyTimelineEngine()
    event = CorporateEvent(
        event_id="EVT-001",
        symbol="RELIANCE.NS",
        event_type="ACQUISITION",
        title="Retail Expansion",
        description="Acquired strategic retail assets nationwide.",
        date="2018-05-15",
        impact_score=0.85,
    )
    timeline_engine.add_event(event)
    events = timeline_engine.get_timeline("RELIANCE.NS")
    assert len(events) == 1
    assert events[0].title == "Retail Expansion"

    # Test Prediction Ledger
    ledger = PredictionLedger()
    pred = PredictionRecord(
        prediction_id="PRED-001",
        symbol="RELIANCE.NS",
        thesis="Strong free cash flow generation and margin expansion.",
        signal="BUY",
        confidence=0.89,
        target_price=3200.0,
        horizon_months=12,
    )
    ledger.record_prediction(pred)

    preds = ledger.get_predictions("RELIANCE.NS")
    assert len(preds) == 1
    assert preds[0].outcome_status == "PENDING"

    evaluated = ledger.evaluate_prediction("RELIANCE.NS", "PRED-001", actual_return=18.5)
    assert evaluated.outcome_status == "SUCCESSFUL"
    assert evaluated.outcome_actual_return == 18.5
