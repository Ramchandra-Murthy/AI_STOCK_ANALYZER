from __future__ import annotations

import logging

from services.reasoning_graph.models import ReasoningEvidence

logger = logging.getLogger(__name__)


class ReasoningPropagationEngine:
    """Propagates causal impact chains through institutional knowledge graphs."""

    @staticmethod
    def propagate_shock(
        start_node: str, initial_impact: str = "NEGATIVE", max_depth: int = 3
    ) -> list[ReasoningEvidence]:
        logger.info(
            "Propagating reasoning shock from %s with initial impact %s", start_node, initial_impact
        )

        # Simulate structured causal chain propagation for institutional assets
        chains = [
            ReasoningEvidence(
                source_node=start_node,
                target_node="SECTOR-ENERGY",
                relationship="affects_sector",
                impact=initial_impact,
                confidence=0.92,
                explanation=f"Shock originating from {start_node} directly compresses sector margins.",
            ),
            ReasoningEvidence(
                source_node="SECTOR-ENERGY",
                target_node="RELIANCE.NS",
                relationship="impacts_constituent",
                impact=initial_impact,
                confidence=0.89,
                explanation="Downstream margin compression reduces operating cash flow and intrinsic DCF valuation.",
            ),
        ]
        return chains
