from services.validation.backtest_engine import (
    BacktestResult,
    InstitutionalBacktestEngine,
)

def test_block21b_positive_signal_validation():
    engine = InstitutionalBacktestEngine()
    result = engine.evaluate_signal(
        symbol="INFY.NS",
        signal_date="2026-01-01",
        entry_price=1000.0,
        exit_price=1150.0,
        model_attribution={
            "DCF": 0.40,
            "Relative": 0.30,
            "Quality": 0.30,
        },
    )
    assert isinstance(result, BacktestResult)
    assert result.symbol == "INFY.NS"
    assert result.entry_price == 1000.0
    assert result.exit_price == 1150.0
    assert result.return_pct == 15.0
    assert result.accuracy is True
    assert result.holding_period_days == 365
    assert result.model_attribution["DCF"] == 0.40

def test_block21b_negative_signal_validation():
    engine = InstitutionalBacktestEngine()
    result = engine.evaluate_signal(
        symbol="INFY.NS",
        signal_date="2026-01-01",
        entry_price=1000.0,
        exit_price=900.0,
    )
    assert isinstance(result, BacktestResult)
    assert result.return_pct == -10.0
    assert result.accuracy is False

def test_block21b_default_attribution():
    engine = InstitutionalBacktestEngine()
    result = engine.evaluate_signal(
        symbol="RELIANCE.NS",
        signal_date="2026-01-01",
        entry_price=2000.0,
        exit_price=2200.0,
    )
    assert result.model_attribution == {
        "DCF": 0.4,
        "Relative": 0.3,
        "Quality": 0.3,
    }
