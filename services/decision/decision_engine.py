from __future__ import annotations

import logging

from services.decision.models import DecisionOption

logger = logging.getLogger(__name__)


class InstitutionalDecisionEngine:
    """Rank decision options from validated scoring evidence."""

    @staticmethod
    def evaluate_options(
        symbol: str,
        policy_profile: str = "Institutional",
        options: list[DecisionOption] | None = None,
    ) -> list[DecisionOption]:
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        if not normalized_symbol:
            raise ValueError("symbol must be a non-empty string")

        logger.info(
            "Evaluating decision options for %s under policy profile '%s'",
            normalized_symbol,
            policy_profile,
        )

        if options is None:
            return []

        valid_options = [
            option
            for option in options
            if option.action in {"BUY", "HOLD", "SELL"}
            and option.confidence >= 0.0
            and option.expected_return is not None
            and option.downside_risk >= 0.0
        ]
        valid_options.sort(
            key=lambda option: option.expected_return * option.confidence - option.downside_risk,
            reverse=True,
        )
        return valid_options
