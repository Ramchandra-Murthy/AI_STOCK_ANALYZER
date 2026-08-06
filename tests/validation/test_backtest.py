from __future__ import annotations

import pytest
from services.validation.backtest_engine import InstitutionalBacktestEngine

def test_backtest_evaluation() -> None:
    engine = InstitutionalBacktestEngine()
    result = engine.evaluate_signal(
        symbol="RELIANCE.NS",
        signal_date="2025-01-12",
        entry_price=2450.0,
        exit_price=3120.0
    )
    assert result.symbol == "RELIANCE.NS"
    assert result.return_pct > 0
    assert result.accuracy is True
    assert "DCF" in result.model_attribution
