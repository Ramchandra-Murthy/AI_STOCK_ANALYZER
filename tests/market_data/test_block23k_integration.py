from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from services.market_data.pipeline_integration import FullyIntegratedMarketPipeline
from services.market_data.confidence_trace import ConfidenceDecisionTraceRecord


class FakeTicker:
    def history(self, **kwargs):
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        return pd.DataFrame(
            {
                "Open": [3480.0, 3500.0],
                "High": [3510.0, 3525.0],
                "Low": [3475.0, 3495.0],
                "Close": [3495.0, 3520.0],
                "Volume": [9000, 12000],
            },
            index=pd.DatetimeIndex([now, now]),
        )

    @property
    def fast_info(self):
        return {"last_price": 3520.0, "previous_close": 3495.0}


def fake_ticker_factory(symbol: str):
    assert symbol == "RELIANCE.NS"
    return FakeTicker()


def test_block23k_fully_integrated_pipeline_execution():
    pipeline = FullyIntegratedMarketPipeline(policy_profile="Institutional")
    packet, decision, result, trace = pipeline.evaluate_stock_securely(
        "RELIANCE.NS",
        ticker_factory=fake_ticker_factory,
    )

    assert packet.current_price == 3520.0
    assert decision.directive == "USE_LIVE"
    assert decision.allowed_in_scoring is True
    assert isinstance(trace, ConfidenceDecisionTraceRecord)
    assert trace.symbol == "RELIANCE.NS"
    assert trace.base_confidence == 0.85
    assert trace.confidence_penalty == 0.0
    assert result is not None
