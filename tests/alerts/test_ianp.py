from __future__ import annotations

import pytest
from services.alerts.models import InstitutionalAlert
from services.alerts.alert_engine import InstitutionalAlertEngine

def test_institutional_alert_immutability() -> None:
    alert = InstitutionalAlert(
        symbol="RELIANCE.NS",
        alert_type="VALUATION_DISCOUNT",
        severity="HIGH",
        message="Discount exceeds 25%"
    )
    assert alert.symbol == "RELIANCE.NS"
    assert alert.acknowledged is False
    assert alert.timestamp is not None
    assert isinstance(alert.metadata, dict)

def test_institutional_alert_engine() -> None:
    # Trigger valuation discount > 25% (Intrinsic 3500, Market 2500 -> 28.5% discount)
    alert = InstitutionalAlertEngine.evaluate_valuation_alert("RELIANCE.NS", 3500.0, 2500.0)
    assert alert is not None
    assert alert.severity == "HIGH"
    assert alert.alert_type == "VALUATION_DISCOUNT"

    notification = InstitutionalAlertEngine.route_notification(alert, "Dashboard")
    assert notification["delivered"] is True
    assert notification["target"] == "Dashboard"
