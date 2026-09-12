from __future__ import annotations

import concurrent.futures
import logging
from typing import Any

logger = logging.getLogger("eros.quantitative.batch_screener")


class EROSMultiAssetBatchScreener:
    """
    Enterprise batch screening engine for EROS 3.0.

    Uses the existing FullyIntegratedMarketPipeline without
    modifying its return contract.

    The pipeline result contract is consumed by index:
        result[0] -> market packet
        result[2] -> unified decision result

    Additional pipeline return elements are intentionally preserved
    by the pipeline and are not unpacked here.
    """

    def __init__(
        self,
        policy_profile: str = "Institutional",
        max_workers: int = 4,
    ) -> None:

        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")

        self.policy_profile = policy_profile
        self.max_workers = max_workers

        logger.info(
            "Initializing EROSMultiAssetBatchScreener " "[policy=%s, max_workers=%d]",
            policy_profile,
            max_workers,
        )

    def evaluate_symbol(self, symbol: str) -> dict[str, Any]:
        """
        Evaluate one security through the existing integrated pipeline.

        A failure for one security is isolated from the remaining universe.
        """

        normalized_symbol = str(symbol).strip().upper()

        if not normalized_symbol:
            return {
                "symbol": normalized_symbol,
                "status": "ERROR",
                "error": "Empty symbol",
            }

        try:
            from services.market_data.pipeline_integration import (
                FullyIntegratedMarketPipeline,
            )

            pipeline = FullyIntegratedMarketPipeline(policy_profile=self.policy_profile)

            pipeline_result = pipeline.evaluate_stock_securely(normalized_symbol)

            if not hasattr(pipeline_result, "__getitem__"):
                raise TypeError("evaluate_stock_securely returned a non-indexable result")

            if len(pipeline_result) < 3:
                raise ValueError("evaluate_stock_securely returned fewer than 3 elements")

            # Certified existing pipeline contract.
            market_packet = pipeline_result[0]
            decision_result = pipeline_result[2]

            decision = decision_result.decision

            return {
                "symbol": normalized_symbol,
                "status": "SUCCESS",
                "price": market_packet.current_price,
                "source": market_packet.details.get("source"),
                "is_stale": market_packet.is_stale,
                "final_action": decision_result.final_action,
                "confidence": decision_result.adjusted_confidence,
                "target_weight": getattr(
                    decision,
                    "target_weight",
                    0.05,
                ),
            }

        except Exception as exc:
            logger.exception(
                "Failed evaluation for symbol %s",
                normalized_symbol,
            )

            return {
                "symbol": normalized_symbol,
                "status": "ERROR",
                "error": str(exc),
            }

    def run_universe_screen(
        self,
        symbols: list[str],
    ) -> list[dict[str, Any]]:
        """
        Run parallel screening across the supplied universe.

        Duplicate symbols are removed while preserving input order.
        Results are sorted deterministically by symbol.
        """

        if not symbols:
            return []

        normalized_symbols: list[str] = []
        seen = set()

        for symbol in symbols:
            normalized_symbol = str(symbol).strip().upper()

            if normalized_symbol and normalized_symbol not in seen:
                normalized_symbols.append(normalized_symbol)
                seen.add(normalized_symbol)

        logger.info(
            "Starting universe screen for %d symbols: %s",
            len(normalized_symbols),
            normalized_symbols,
        )

        results: list[dict[str, Any]] = []

        worker_count = min(
            self.max_workers,
            max(1, len(normalized_symbols)),
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:

            future_to_symbol = {
                executor.submit(
                    self.evaluate_symbol,
                    symbol,
                ): symbol
                for symbol in normalized_symbols
            }

            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]

                try:
                    result = future.result()

                except Exception as exc:
                    logger.exception(
                        "Unhandled future failure for %s",
                        symbol,
                    )

                    result = {
                        "symbol": symbol,
                        "status": "ERROR",
                        "error": str(exc),
                    }

                results.append(result)

        results.sort(key=lambda item: item.get("symbol", ""))

        success_count = sum(1 for item in results if item.get("status") == "SUCCESS")

        error_count = len(results) - success_count

        logger.info(
            "Universe screen completed: total=%d success=%d errors=%d",
            len(results),
            success_count,
            error_count,
        )

        return results


__all__ = [
    "EROSMultiAssetBatchScreener",
]
