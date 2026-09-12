from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


class EROSBlock102FrontendContract:
    """
    EROS 3.0 Block 102

    Presentation-only contract layer for the verified Block 94 -> 101
    quantitative/execution chain.

    This class MUST NOT:
      - mutate portfolio state
      - mutate valuation/performance/risk state
      - create orders
      - submit to broker
      - perform live execution

    It converts already-produced block outputs into a UI-safe read model.
    """

    BLOCK_ID = "102"
    ENGINE_VERSION = "EROS-3.0-BLOCK-102"

    SAFETY_FIELDS = {
        "portfolio_mutation": False,
        "valuation_mutation": False,
        "performance_mutation": False,
        "risk_mutation": False,
        "optimization": False,
        "order_creation": False,
        "broker_submission": False,
        "live_order_submission": False,
        "execution_blocked": True,
        "non_mutation_invariant": True,
    }

    BLOCK_NAMES = {
        "94": "Stress Scenario Engine",
        "95": "Stress Evidence Gate",
        "96": "Stress Decision Gate",
        "97": "Stress Readiness Gate",
        "98": "Execution Governance Bridge",
        "99": "Execution Intent Authorization",
        "100": "Paper Execution / Fill Validation",
        "101": "Execution Evidence Reconciliation",
    }

    def __init__(self) -> None:
        self.engine_version = self.ENGINE_VERSION

    def build(
        self,
        *,
        block94: Mapping[str, Any] | None = None,
        block95: Mapping[str, Any] | None = None,
        block96: Mapping[str, Any] | None = None,
        block97: Mapping[str, Any] | None = None,
        block98: Mapping[str, Any] | None = None,
        block99: Mapping[str, Any] | None = None,
        block100: Mapping[str, Any] | None = None,
        block101: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:

        blocks = {
            "94": deepcopy(dict(block94 or {})),
            "95": deepcopy(dict(block95 or {})),
            "96": deepcopy(dict(block96 or {})),
            "97": deepcopy(dict(block97 or {})),
            "98": deepcopy(dict(block98 or {})),
            "99": deepcopy(dict(block99 or {})),
            "100": deepcopy(dict(block100 or {})),
            "101": deepcopy(dict(block101 or {})),
        }

        pipeline = []

        for block_id, payload in blocks.items():
            pipeline.append(
                {
                    "block_id": block_id,
                    "name": self.BLOCK_NAMES[block_id],
                    "status": self._status(payload),
                    "source_block": payload.get("source_block"),
                    "identifier": self._identifier(payload),
                    "execution_blocked": payload.get(
                        "execution_blocked",
                        True,
                    ),
                }
            )

        governance = blocks["98"]
        intent = blocks["99"]
        execution = blocks["100"]
        reconciliation = blocks["101"]

        result = {
            "status": "CERTIFIED",
            "block_id": self.BLOCK_ID,
            "engine_version": self.engine_version,
            "created_at": datetime.now(UTC).isoformat(),
            "pipeline_status": pipeline,
            "risk": {
                "stress_status": self._status(blocks["94"]),
                "evidence_status": self._status(blocks["95"]),
                "decision_status": self._status(blocks["96"]),
                "readiness_status": self._status(blocks["97"]),
                "scenario_count": blocks["94"].get(
                    "scenario_count",
                    blocks["97"].get("scenario_count"),
                ),
                "downside_pnl": blocks["94"].get("downside_pnl"),
                "upside_pnl": blocks["94"].get("upside_pnl"),
            },
            "governance": {
                "status": governance.get(
                    "governance_status",
                    self._status(governance),
                ),
                "governance_id": governance.get("governance_id"),
                "execution_action": governance.get(
                    "execution_action",
                    governance.get("action"),
                ),
                "source_readiness_id": governance.get("source_readiness_id"),
                "source_decision_id": governance.get("source_decision_id"),
                "source_gate_id": governance.get("source_gate_id"),
                "source_certificate_id": governance.get("source_certificate_id"),
            },
            "intent": {
                "status": intent.get(
                    "intent_status",
                    self._status(intent),
                ),
                "intent_id": intent.get("intent_id"),
                "intent_action": intent.get("intent_action"),
                "authorization_status": intent.get("authorization_status"),
                "symbol": intent.get("symbol"),
                "action": intent.get("action"),
                "quantity": intent.get("quantity"),
                "reference_price": intent.get("reference_price"),
            },
            "execution": {
                "status": execution.get(
                    "execution_status",
                    self._status(execution),
                ),
                "execution_id": execution.get("execution_id"),
                "symbol": execution.get("symbol"),
                "action": execution.get("action"),
                "requested_quantity": execution.get("requested_quantity"),
                "filled_quantity": execution.get("filled_quantity"),
                "reference_price": execution.get("reference_price"),
                "fill_price": execution.get("fill_price"),
                "fill_status": execution.get("fill_status"),
                "slippage_bps": execution.get("slippage_bps"),
                "transaction_cost": execution.get("transaction_cost"),
                "net_value": execution.get("net_value"),
            },
            "reconciliation": {
                "status": reconciliation.get(
                    "reconciliation_status",
                    self._status(reconciliation),
                ),
                "reconciliation_id": reconciliation.get("reconciliation_id"),
                "source_execution_id": reconciliation.get("source_execution_id"),
                "quantity_reconciled": reconciliation.get("quantity_reconciled"),
                "price_reconciled": reconciliation.get("price_reconciled"),
                "value_reconciled": reconciliation.get("value_reconciled"),
                "cost_reconciled": reconciliation.get("cost_reconciled"),
                "lineage_reconciled": reconciliation.get("lineage_reconciled"),
            },
            "lineage": {
                "block94": self._identifier(blocks["94"]),
                "block95": self._identifier(blocks["95"]),
                "block96": self._identifier(blocks["96"]),
                "block97": self._identifier(blocks["97"]),
                "block98": self._identifier(blocks["98"]),
                "block99": self._identifier(blocks["99"]),
                "block100": self._identifier(blocks["100"]),
                "block101": self._identifier(blocks["101"]),
            },
            "safety": deepcopy(self.SAFETY_FIELDS),
        }

        return self._validate(result)

    def snapshot(self, **kwargs: Any) -> dict[str, Any]:
        return self.build(**kwargs)

    @staticmethod
    def _status(payload: Mapping[str, Any]) -> Any:
        return payload.get("status")

    @staticmethod
    def _identifier(payload: Mapping[str, Any]) -> Any:
        for field in (
            "certificate_id",
            "gate_id",
            "decision_id",
            "readiness_id",
            "governance_id",
            "intent_id",
            "execution_id",
            "reconciliation_id",
        ):
            value = payload.get(field)
            if value:
                return value
        return None

    def _validate(self, result: dict[str, Any]) -> dict[str, Any]:
        safety = result["safety"]

        for field, expected in self.SAFETY_FIELDS.items():
            if safety.get(field) is not expected:
                raise ValueError(f"BLOCK102_SAFETY_INVARIANT_FAILED:{field}")

        if result["block_id"] != "102":
            raise ValueError("INVALID_BLOCK_ID")

        if result["status"] != "CERTIFIED":
            raise ValueError("INVALID_FRONTEND_STATUS")

        if len(result["pipeline_status"]) != 8:
            raise ValueError("INVALID_PIPELINE_LENGTH")

        return result
