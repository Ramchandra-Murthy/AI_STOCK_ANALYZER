from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("eros.quantitative.portfolio_optimizer")


class EROSPortfolioOptimizer:
    """
    Deterministic institutional portfolio allocation engine.

    Consumes certified EROS batch screener results and converts
    target weights into a normalized portfolio allocation.

    The optimizer does not fetch market data and does not modify
    the existing market-data or decision pipeline.
    """

    def __init__(
        self,
        policy_profile: str = "Institutional",
        max_position_weight: float = 0.25,
        min_position_weight: float = 0.0,
        target_total_weight: float = 1.0,
    ) -> None:

        if not 0.0 <= min_position_weight <= 1.0:
            raise ValueError("min_position_weight must be between 0 and 1")

        if not 0.0 < max_position_weight <= 1.0:
            raise ValueError("max_position_weight must be between 0 and 1")

        if min_position_weight > max_position_weight:
            raise ValueError("min_position_weight cannot exceed max_position_weight")

        if not 0.0 <= target_total_weight <= 1.0:
            raise ValueError("target_total_weight must be between 0 and 1")

        self.policy_profile = policy_profile
        self.max_position_weight = max_position_weight
        self.min_position_weight = min_position_weight
        self.target_total_weight = target_total_weight

    @staticmethod
    def _normalize_symbol(symbol: Any) -> str:
        return str(symbol).strip().upper()

    @staticmethod
    def _valid_number(value: Any) -> bool:
        try:
            number = float(value)
            return number == number and number >= 0.0
        except (TypeError, ValueError):
            return False

    def _extract_candidates(
        self,
        screening_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        candidates: list[dict[str, Any]] = []
        seen = set()

        for item in screening_results:

            if not isinstance(item, dict):
                continue

            symbol = self._normalize_symbol(item.get("symbol", ""))

            if not symbol or symbol in seen:
                continue

            seen.add(symbol)

            if item.get("status") != "SUCCESS":
                continue

            raw_weight = item.get("target_weight", 0.0)

            if not self._valid_number(raw_weight):
                continue

            raw_weight = float(raw_weight)

            if raw_weight <= 0.0:
                continue

            candidates.append(
                {
                    "symbol": symbol,
                    "raw_weight": raw_weight,
                    "confidence": float(item.get("confidence", 0.0) or 0.0),
                    "final_action": item.get(
                        "final_action",
                        "HOLD",
                    ),
                    "price": item.get("price"),
                    "source": item.get("source"),
                    "is_stale": bool(item.get("is_stale", False)),
                }
            )

        return candidates

    def optimize(
        self,
        screening_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        if screening_results is None:
            return []

        if not isinstance(screening_results, list):
            raise TypeError("screening_results must be a list")

        candidates = self._extract_candidates(screening_results)

        if not candidates:
            return []

        raw_total = sum(item["raw_weight"] for item in candidates)

        if raw_total <= 0.0:
            return []

        target_total = self.target_total_weight

        weights = {
            item["symbol"]: (item["raw_weight"] / raw_total) * target_total for item in candidates
        }

        for _ in range(len(weights) + 2):

            capped = {
                symbol: weight
                for symbol, weight in weights.items()
                if weight > self.max_position_weight
            }

            if not capped:
                break

            excess = sum(weight - self.max_position_weight for weight in capped.values())

            for symbol in capped:
                weights[symbol] = self.max_position_weight

            eligible = [
                symbol for symbol, weight in weights.items() if weight < self.max_position_weight
            ]

            if not eligible or excess <= 0:
                break

            eligible_total = sum(weights[symbol] for symbol in eligible)

            if eligible_total <= 0:
                break

            for symbol in eligible:
                share = weights[symbol] / eligible_total

                weights[symbol] += excess * share

        if self.min_position_weight > 0.0:

            eligible_symbols = list(weights.keys())

            if len(eligible_symbols) * self.min_position_weight <= target_total:

                for symbol in eligible_symbols:
                    if 0.0 < weights[symbol] < self.min_position_weight:
                        weights[symbol] = self.min_position_weight

                current_total = sum(weights.values())

                if current_total > target_total:
                    scale = target_total / current_total

                    for symbol in weights:
                        weights[symbol] *= scale

        results: list[dict[str, Any]] = []

        for item in candidates:

            symbol = item["symbol"]
            optimized_weight = float(weights.get(symbol, 0.0))

            results.append(
                {
                    "symbol": symbol,
                    "status": "SUCCESS",
                    "raw_weight": item["raw_weight"],
                    "optimized_weight": optimized_weight,
                    "allocation_pct": (optimized_weight * 100.0),
                    "confidence": item["confidence"],
                    "final_action": item["final_action"],
                    "price": item["price"],
                    "source": item["source"],
                    "is_stale": item["is_stale"],
                }
            )

        results.sort(key=lambda item: item["symbol"])

        return results

    def summarize(
        self,
        optimized_results: list[dict[str, Any]],
    ) -> dict[str, Any]:

        total_weight = sum(float(item.get("optimized_weight", 0.0)) for item in optimized_results)

        return {
            "policy_profile": self.policy_profile,
            "security_count": len(optimized_results),
            "total_weight": total_weight,
            "cash_weight": max(
                0.0,
                1.0 - total_weight,
            ),
            "status": "SUCCESS",
        }


__all__ = [
    "EROSPortfolioOptimizer",
]
