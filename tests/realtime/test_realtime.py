from __future__ import annotations

import pytest
from services.realtime.stream import MarketEvent, RealTimeEventDispatcher
from services.realtime.alert_engine import RealTimeAlertEngine

def test_real_time_intelligence_platform() -> None:
    dispatcher = RealTimeEventDispatcher()
    
    event = MarketEvent(
        event_id="EVT-001",
        event_type="EARNINGS_RELEASE",
        symbol="RELIANCE.NS",
        payload={"revenue_growth": 0.14, "net_margin": 0.19},
        priority=1,
        source="NSEFeed"
    )
    
    result = dispatcher.dispatch(event)
    assert result["status"] == "PROCESSED"
    assert result["action_triggered"] == "TRIGGER_FULL_RESEARCH_PIPELINE"

    alert = RealTimeAlertEngine.evaluate_alert("RELIANCE.NS", 2100.0, 3200.0)
    assert alert is not None
    assert alert.severity == "HIGH"
    assert alert.category == "VALUATION"
    assert "discount" in alert.message
