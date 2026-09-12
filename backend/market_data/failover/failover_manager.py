from __future__ import annotations

import logging
from typing import Any

from backend.market_data.providers.base import ProviderRegistry

logger = logging.getLogger(__name__)


class ProviderFailoverManager:
    """Manages multi-tier provider failover for high-availability quote retrieval."""

    def __init__(self, provider_chain: list[str]) -> None:
        self.provider_chain = provider_chain

    def get_quote_with_failover(self, symbol: str) -> dict[str, Any]:
        last_exception = None
        for provider_name in self.provider_chain:
            try:
                provider = ProviderRegistry.get(provider_name)
                quote = provider.get_quote(symbol)
                logger.info(
                    "Successfully fetched quote for %s using provider tier '%s'",
                    symbol,
                    provider_name,
                )
                return quote
            except Exception as e:
                logger.warning(
                    "Provider '%s' failed for symbol %s: %s. Attempting failover...",
                    provider_name,
                    symbol,
                    e,
                )
                last_exception = e

        logger.error("All providers in failover chain failed for symbol %s", symbol)
        raise RuntimeError(f"All providers failed for symbol {symbol}: {last_exception}")
