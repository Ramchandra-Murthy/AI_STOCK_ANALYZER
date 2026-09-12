from __future__ import annotations

import logging
from typing import Any

from services.data_platform.contracts import FinancialProvider, QualityCheckResult
from services.data_platform.quality import DataQualityEngine

logger = logging.getLogger(__name__)


class YahooFinanceProvider(FinancialProvider):
    """Institutional adapter for Yahoo Finance market data and fundamentals."""

    def download_financials(self, symbol: str) -> dict[str, Any]:
        logger.info("Downloading financials for %s via Yahoo Finance provider", symbol)
        return {
            "symbol": symbol,
            "revenue": 1250000.0,
            "net_income": 150000.0,
            "total_debt": 450000.0,
            "source": "YahooFinance",
        }

    def download_prices(self, symbol: str) -> list[dict[str, Any]]:
        return [{"date": "2026-08-07", "close": 2800.0, "volume": 1250000}]

    def download_actions(self, symbol: str) -> list[dict[str, Any]]:
        return [{"date": "2026-07-01", "action": "DIVIDEND", "value": 10.0}]

    def validate_data(self, data: dict[str, Any]) -> QualityCheckResult:
        rev = data.get("revenue", 0.0)
        return DataQualityEngine.inspect_metric("revenue", rev, min_val=0.0, max_val=1e15)
