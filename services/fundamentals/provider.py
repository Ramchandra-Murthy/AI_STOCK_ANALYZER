from __future__ import annotations

import logging
from typing import Any
from services.fundamentals.models import FinancialStatements

logger = logging.getLogger(__name__)


class FinancialDataProvider:
    """Provider responsible for fetching raw financial statements from external data sources."""

    def fetch_raw_financials(self, symbol: str) -> dict[str, Any]:
        logger.info("Fetching raw financial statements for symbol: %s", symbol)
        return {
            "symbol": symbol,
            "statements": []
        }
