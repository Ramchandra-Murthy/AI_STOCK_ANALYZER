import pandas as pd
import pytest

from algorithmic_trading.pipeline import analyze_symbol


def _market_frame() -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=80, freq="D")
    close = pd.Series(range(100, 180), index=index, dtype=float)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": 100_000,
        }
    )


def test_pipeline_combines_algorithmic_components() -> None:
    frame = _market_frame()
    benchmark = pd.Series(
        range(100, 140),
        index=pd.date_range("2026-01-01", periods=40, freq="2D"),
        dtype=float,
    )
    trade_returns = pd.Series([0.02, -0.01, 0.03, 0.01])

    result = analyze_symbol(
        "RELIANCE",
        frame,
        benchmark,
        capital=100_000,
        risk_fraction=0.01,
        stop_price=175,
        historical_trade_returns=trade_returns,
    )

    assert result.symbol == "RELIANCE"
    assert result.regime in {"BULLISH", "BEARISH", "INCONCLUSIVE"}
    assert result.signal.direction in {"LONG", "SHORT", "FLAT"}
    assert result.edge is not None
    assert result.position_size.quantity >= 0


def test_pipeline_rejects_missing_close() -> None:
    with pytest.raises(ValueError, match="Close"):
        analyze_symbol(
            "TCS",
            pd.DataFrame({"Open": [100.0]}),
            None,
            capital=100_000,
        )


from algorithmic_trading.trading_profile import TradingProfile


def test_pipeline_uses_profile_risk_engine_and_exposes_plan() -> None:
    frame = _market_frame()
    profile = TradingProfile(
        capital=100_000,
        risk_value=1,
        max_position_pct=50,
        max_exposure_pct=80,
        cash_reserve_pct=0,
        stop_mode="percentage",
        stop_value=2,
        estimated_round_trip_cost_pct=0,
    )

    result = analyze_symbol(
        "RELIANCE",
        frame,
        None,
        profile=profile,
        available_cash=60_000,
        current_exposure=10_000,
    )

    assert result.risk_plan is not None
    assert result.risk_plan.allowed
    assert result.position_size.method == "profile_risk"
    assert result.position_size.quantity == result.risk_plan.quantity
    assert result.risk_plan.capital_required <= 50_000
    assert result.risk_plan.estimated_loss_at_stop <= profile.risk_budget


def test_profile_daily_loss_limit_blocks_pipeline_position() -> None:
    frame = _market_frame()
    profile = TradingProfile(
        capital=100_000,
        max_daily_loss_pct=2,
        stop_mode="percentage",
        stop_value=2,
    )

    result = analyze_symbol(
        "RELIANCE",
        frame,
        None,
        profile=profile,
        daily_loss_so_far=2_000,
    )

    assert result.risk_plan is not None
    assert not result.risk_plan.allowed
    assert result.position_size.quantity == 0


def test_profile_pipeline_requires_technical_stop() -> None:
    frame = _market_frame()
    profile = TradingProfile(stop_mode="technical")

    with pytest.raises(ValueError, match="stop_price is required"):
        analyze_symbol("RELIANCE", frame, None, profile=profile)
