from __future__ import annotations

import logging
from typing import Any

from backend.providers.base_provider import BaseDataProvider, ProviderError

logger = logging.getLogger(__name__)


class ProviderSelectionEngine:
    """Manages multi-provider failover, fallback routing, and health checks."""

    def __init__(self, providers: list[BaseDataProvider]) -> None:
        self.providers = providers

    def execute_with_failover(
        self, method_name: str, symbol: str, *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        last_error = None
        for provider in self.providers:
            if not provider.check_health():
                logger.warning("Provider %s is unhealthy. Skipping...", provider.provider_name)
                continue
            try:
                method = getattr(provider, method_name)
                logger.info(
                    "Routing data request '%s' to provider %s", method_name, provider.provider_name
                )
                return method(symbol, *args, **kwargs)
            except Exception as e:
                logger.warning(
                    "Provider %s failed for %s: %s. Failing over...",
                    provider.provider_name,
                    symbol,
                    str(e),
                )
                last_error = e

        raise ProviderError(
            f"All data providers failed for operation '{method_name}' on symbol '{symbol}'. Last error: {str(last_error)}"
        )
