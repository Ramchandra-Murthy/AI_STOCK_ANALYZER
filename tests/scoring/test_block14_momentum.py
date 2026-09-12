from services.market_data.models import PriceRecord
from services.scoring.technical import (
    MomentumScoringEngine,
    TechnicalIndicatorEngine,
)


def _records(count: int = 60):
    records = []
    for i in range(count):
        close = 100.0 + (i * 2.0)
        records.append(
            PriceRecord(
                date=f"2026-01-{(i % 28) + 1:02d}",
                open=close - 1.0,
                high=close + 2.0,
                low=close - 2.0,
                close=close,
                volume=100000 + i * 1000,
            )
        )
    return records


def test_block14_technical_indicator_engine():
    records = _records()
    engine = TechnicalIndicatorEngine()
    result = engine.calculate(records)
    assert result.sma_20 > 0
    assert result.sma_50 > 0
    assert result.sma_200 > 0
    assert 0.0 <= result.rsi_14 <= 100.0
    assert isinstance(result.macd, float)
    assert isinstance(result.macd_signal, float)
    assert isinstance(result.macd_histogram, float)
    assert 0.0 <= result.trend_score <= 100.0
    assert 0.0 <= result.relative_strength_score <= 100.0
    assert 0.0 <= result.breakout_score <= 100.0
    assert 0.0 <= result.momentum_score <= 100.0


def test_block14_momentum_scoring_engine():
    records = _records()
    engine = MomentumScoringEngine()
    result = engine.evaluate(
        symbol="RELIANCE.NS",
        records=records,
    )
    assert result.symbol == "RELIANCE.NS"
    assert 0.0 <= result.momentum_score <= 100.0
    assert 0.0 <= result.trend_score <= 100.0
    assert 0.0 <= result.rsi_score <= 100.0
    assert 0.0 <= result.macd_score <= 100.0
    assert 0.0 <= result.moving_average_score <= 100.0
    assert 0.0 <= result.relative_strength_score <= 100.0
    assert 0.0 <= result.breakout_score <= 100.0
    assert result.details["engine_version"] == "EROS-3.0-BLOCK-14"
    assert result.details["records_analyzed"] == len(records)
