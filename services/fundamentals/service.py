from __future__ import annotations

import logging
from typing import Any
from services.fundamentals.provider import FinancialDataProvider
from services.fundamentals.parser import FinancialStatementsParser
from services.fundamentals.models import FinancialStatements

logger = logging.getLogger(__name__)


class FundamentalsService:
    """Service managing retrieval, parsing, and normalization of financial statements."""

    def __init__(self, provider: FinancialDataProvider, parser: FinancialStatementsParser) -> None:
        self._provider = provider
        self._parser = parser

    def get_financial_statements(self, symbol: str) -> FinancialStatements:
        raw = self._provider.fetch_raw_financials(symbol)
        statements = self._parser.parse(raw)
        logger.info("Successfully normalized financial statements for symbol: %s", symbol)
        return statements
