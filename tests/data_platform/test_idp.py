from __future__ import annotations

import pytest
from services.data_platform.quality import DataQualityEngine
from services.data_platform.providers.yahoo import YahooFinanceProvider

def test_institutional_data_platform() -> None:
    # Test Data Quality Engine
    check = DataQualityEngine.inspect_metric("operating_margin", 18.5, min_val=-100.0, max_val=100.0)
    assert check.passed is True
    assert check.confidence > 0.90

    # Test Yahoo Provider and Validation Contract
    provider = YahooFinanceProvider()
    fin = provider.download_financials("RELIANCE.NS")
    assert fin["symbol"] == "RELIANCE.NS"
    assert fin["revenue"] > 0.0

    validation = provider.validate_data(fin)
    assert validation.passed is True
    assert validation.metric_name == "revenue"
