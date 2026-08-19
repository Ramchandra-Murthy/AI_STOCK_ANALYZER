from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping


class EROSBlock104CommandCenter:
    """
    EROS 3.0 Block 104

    Institutional Command Center presentation model.

    Presentation-only layer consuming the Block 103
    Institutional Frontend Read Model.

    This block MUST NOT:
        - create orders
        - submit broker orders
        - perform live execution
        - mutate portfolio
        - mutate valuation
        - mutate performance
        - mutate risk
        - perform optimization
    """

    BLOCK_ID = "104"
    ENGINE_VERSION = "EROS-3.0-BLOCK-104"

    SOURCE_BLOCK = "103"

    def __init__(self) -> None:
        self.engine_version = self.ENGINE_VERSION

    def render_model(
        self,
        *,
        read_model: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert the Block 103 read model into a UI-ready
        institutional command-center model.
        """

        source = deepcopy(dict(read_model))

        self._validate_source(source)

        return {
            "status": "CERTIFIED",
            "block_id": self.BLOCK_ID,
            "engine_version": self.engine_version,
            "source_block": self.SOURCE_BLOCK,

            "header": {
                "title": "EROS 3.0 Institutional Command Center",
                "subtitle": (
                    "Read-only governance, execution and "
                    "reconciliation control view"
                ),
                "pipeline": "94 -> 103",
            },

            "status_cards": {
                "governance": source["governance"].get("status"),
                "intent": source["intent"].get("status"),
                "execution": source["execution"].get("status"),
                "reconciliation": source["reconciliation"].get(
                    "status"
                ),
            },

            "pipeline": deepcopy(
                source.get("pipeline", [])
            ),

            "risk": deepcopy(
                source.get("risk", {})
            ),

            "governance": deepcopy(
                source.get("governance", {})
            ),

            "intent": deepcopy(
                source.get("intent", {})
            ),

            "execution": deepcopy(
                source.get("execution", {})
            ),

            "reconciliation": deepcopy(
                source.get("reconciliation", {})
            ),

            "lineage": deepcopy(
                source.get("lineage", {})
            ),

            "safety": {
                "portfolio_mutation": source["safety"].get(
                    "portfolio_mutation"
                ),
                "valuation_mutation": source["safety"].get(
                    "valuation_mutation"
                ),
                "performance_mutation": source["safety"].get(
                    "performance_mutation"
                ),
                "risk_mutation": source["safety"].get(
                    "risk_mutation"
                ),
                "optimization": source["safety"].get(
                    "optimization"
                ),
                "order_creation": source["safety"].get(
                    "order_creation"
                ),
                "broker_submission": source["safety"].get(
                    "broker_submission"
                ),
                "live_order_submission": source["safety"].get(
                    "live_order_submission"
                ),
                "execution_blocked": source["safety"].get(
                    "execution_blocked"
                ),
                "non_mutation_invariant": source["safety"].get(
                    "non_mutation_invariant"
                ),
            },

            "ui_policy": {
                "read_only": True,
                "allow_order_creation": False,
                "allow_broker_submission": False,
                "allow_live_execution": False,
                "allow_portfolio_mutation": False,
                "allow_valuation_mutation": False,
                "allow_performance_mutation": False,
                "allow_risk_mutation": False,
                "allow_optimization": False,
            },
        }

    def snapshot(
        self,
        *,
        read_model: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return self.render_model(
            read_model=read_model
        )

    @staticmethod
    def _validate_source(
        source: Mapping[str, Any],
    ) -> None:

        if source.get("status") != "CERTIFIED":
            raise ValueError(
                "BLOCK104_SOURCE_NOT_CERTIFIED"
            )

        if str(source.get("block_id")) != "103":
            raise ValueError(
                "BLOCK104_INVALID_SOURCE_BLOCK"
            )

        required_sections = (
            "pipeline",
            "governance",
            "intent",
            "execution",
            "reconciliation",
            "lineage",
            "safety",
        )

        for section in required_sections:
            if not isinstance(
                source.get(section),
                Mapping,
            ) and section != "pipeline":
                raise ValueError(
                    f"BLOCK104_MISSING_{section.upper()}"
                )

        if not isinstance(
            source.get("pipeline"),
            list,
        ):
            raise ValueError(
                "BLOCK104_INVALID_PIPELINE"
            )

        safety = source["safety"]

        required_false = (
            "portfolio_mutation",
            "valuation_mutation",
            "performance_mutation",
            "risk_mutation",
            "optimization",
            "order_creation",
            "broker_submission",
            "live_order_submission",
        )

        for key in required_false:
            if safety.get(key) is not False:
                raise ValueError(
                    f"BLOCK104_SAFETY_FAILED_{key.upper()}"
                )

        if safety.get(
            "execution_blocked"
        ) is not True:
            raise ValueError(
                "BLOCK104_EXECUTION_BLOCKED_FAILED"
            )

        if safety.get(
            "non_mutation_invariant"
        ) is not True:
            raise ValueError(
                "BLOCK104_NON_MUTATION_FAILED"
            )


def build_command_center(
    read_model: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Convenience function for the Streamlit integration layer.
    """

    return EROSBlock104CommandCenter().render_model(
        read_model=read_model
    )
