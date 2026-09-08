from __future__ import annotations

import logging
import time
from typing import Any, Optional
from core.events.dispatcher import EventDispatcher
from services.fundamentals.events import FundamentalsDownloaded
from services.financials.financial_statement import FinancialStatements
from services.fundamentals.normalizer import FinancialNormalizer
from services.fundamentals.provider import IFundamentalProvider

logger = logging.getLogger(__name__)


class FundamentalsService:
    """Service managing financial statements acquisition, normalization, caching, and event dispatching."""

    def __init__(
        self,
        provider: IFundamentalProvider,
        normalizer: FinancialNormalizer,
        dispatcher: EventDispatcher,
        cache: Optional[dict[str, FinancialStatements]] = None,
    ) -> None:
        self._provider = provider
        self._normalizer = normalizer
        self._dispatcher = dispatcher
        self._cache = cache if cache is not None else {}

    async def get_or_download(self, symbol: str) -> FinancialStatements:
        """Retrieve financial statements from cache or download and normalize them, then dispatch event."""
        if symbol in self._cache:
            logger.info("Serving financial statements from cache for symbol: %s", symbol)
            statements = self._cache[symbol]
        else:
            raw = self._provider.download(symbol)
            statements = self._normalizer.normalize(raw)
            self._cache[symbol] = statements

        event = FundamentalsDownloaded(
            symbol=symbol,
            provider=statements.metadata.get("provider", "YahooFinance"),
            timestamp=time.time(),
            payload={
                "financial_statements": statements,
                "symbol": symbol,
            },
        )

        await self._dispatcher.dispatch(event)
        logger.info("FundamentalsDownloaded event dispatched successfully for symbol: %s", symbol)
        return statements
