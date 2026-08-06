from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable
from services.fundamentals.models import FinancialStatements

logger = logging.getLogger(__name__)


@runtime_checkable
class IFundamentalProvider(Protocol):
    """Protocol defining interface for fundamental data providers."""
    def download(self, symbol: str) -> dict[str, Any]:
        ...


class YahooFinanceProvider:
    """Yahoo Finance adapter implementing IFundamentalProvider."""

    def download(self, symbol: str) -> dict[str, Any]:
        logger.info("Downloading raw financials from Yahoo Finance for symbol: %s", symbol)
        return {
            "symbol": symbol,
            "provider": "YahooFinance",
            "income_statement": {
                "period": "FY2025",
                "revenue": 1000000.0,
                "operating_income": 220000.0,
                "ebit": 200000.0,
                "net_income": 150000.0,
                "eps": 45.5,
            },
            "balance_sheet": {
                "period": "FY2025",
                "total_assets": 3000000.0,
                "total_liabilities": 1200000.0,
                "shareholders_equity": 1800000.0,
                "cash": 300000.0,
                "debt": 500000.0,
            },
            "cash_flow": {
                "period": "FY2025",
                "operating_cash_flow": 250000.0,
                "capex": 80000.0,
                "free_cash_flow": 170000.0,
                "investing_cash_flow": -90000.0,
                "financing_cash_flow": -50000.0,
            },
        }
