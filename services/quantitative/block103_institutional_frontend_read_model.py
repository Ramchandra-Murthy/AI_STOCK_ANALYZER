from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class EROSBlock103InstitutionalFrontendReadModel:
    """
    EROS 3.0 Block 103

    Converts the Block 102 frontend contract into an institutional,
    UI-ready read model.

    Presentation/read-model layer only.
    """

    BLOCK_ID = "103"
    ENGINE_VERSION = "EROS-3.0-BLOCK-103"

    REQUIRED_BLOCKS = (
        "94",
        "95",
        "96",
        "97",
        "98",
        "99",
        "100",
        "101",
    )

    def __init__(self) -> None:
        self.engine_version = self.ENGINE_VERSION

    def build(
        self,
        *,
        contract: Mapping[str, Any],
    ) -> dict[str, Any]:

        source = deepcopy(dict(contract))

        self._validate_source(source)

        pipeline = self._build_pipeline(source)
        risk = self._build_risk(source)
        governance = self._build_governance(source)
        intent = self._build_intent(source)
        execution = self._build_execution(source)
        reconciliation = self._build_reconciliation(source)
        lineage = self._build_lineage(source)
        safety = self._build_safety(source)

        return {
            "status": "CERTIFIED",
            "block_id": self.BLOCK_ID,
            "engine_version": self.engine_version,
            "dashboard": {
                "title": "EROS 3.0 Institutional Command Center",
                "subtitle": "Read-only governance, execution and reconciliation view",
            },
            "pipeline": pipeline,
            "risk": risk,
            "governance": governance,
            "intent": intent,
            "execution": execution,
            "reconciliation": reconciliation,
            "lineage": lineage,
            "safety": safety,
        }

    def snapshot(
        self,
        *,
        contract: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.build(contract=contract)

    @staticmethod
    def _validate_source(source: Mapping[str, Any]) -> None:

        if source.get("status") != "CERTIFIED":
            raise ValueError("BLOCK103_SOURCE_NOT_CERTIFIED")

        if source.get("block_id") != "102":
            raise ValueError("BLOCK103_INVALID_SOURCE_BLOCK")

        pipeline = source.get("pipeline_status")

        if not isinstance(pipeline, list):
            raise ValueError("BLOCK103_PIPELINE_MISSING")

        block_ids = {str(item.get("block_id")) for item in pipeline if isinstance(item, Mapping)}

        if block_ids != set(EROSBlock103InstitutionalFrontendReadModel.REQUIRED_BLOCKS):
            raise ValueError("BLOCK103_INVALID_PIPELINE")

        safety = source.get("safety")

        if not isinstance(safety, Mapping):
            raise ValueError("BLOCK103_SAFETY_MISSING")

        if safety.get("portfolio_mutation") is not False:
            raise ValueError("BLOCK103_PORTFOLIO_MUTATION")

        if safety.get("valuation_mutation") is not False:
            raise ValueError("BLOCK103_VALUATION_MUTATION")

        if safety.get("performance_mutation") is not False:
            raise ValueError("BLOCK103_PERFORMANCE_MUTATION")

        if safety.get("risk_mutation") is not False:
            raise ValueError("BLOCK103_RISK_MUTATION")

        if safety.get("optimization") is not False:
            raise ValueError("BLOCK103_OPTIMIZATION")

        if safety.get("order_creation") is not False:
            raise ValueError("BLOCK103_ORDER_CREATION")

        if safety.get("broker_submission") is not False:
            raise ValueError("BLOCK103_BROKER_SUBMISSION")

        if safety.get("live_order_submission") is not False:
            raise ValueError("BLOCK103_LIVE_EXECUTION")

        if safety.get("execution_blocked") is not True:
            raise ValueError("BLOCK103_EXECUTION_BLOCKED_INVARIANT")

        if safety.get("non_mutation_invariant") is not True:
            raise ValueError("BLOCK103_NON_MUTATION_INVARIANT")

    @staticmethod
    def _build_pipeline(
        source: Mapping[str, Any],
    ) -> list[dict[str, Any]]:

        pipeline = []

        for item in source["pipeline_status"]:
            pipeline.append(
                {
                    "block_id": item.get("block_id"),
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "identifier": item.get("identifier"),
                    "source_block": item.get("source_block"),
                    "execution_blocked": item.get(
                        "execution_blocked",
                        True,
                    ),
                }
            )

        return pipeline

    @staticmethod
    def _build_risk(
        source: Mapping[str, Any],
    ) -> dict[str, Any]:

        risk = source.get("risk", {})

        return {
            "stress_status": risk.get("stress_status"),
            "evidence_status": risk.get("evidence_status"),
            "decision_status": risk.get("decision_status"),
            "readiness_status": risk.get("readiness_status"),
            "scenario_count": risk.get("scenario_count"),
            "downside_pnl": risk.get("downside_pnl"),
            "upside_pnl": risk.get("upside_pnl"),
        }

    @staticmethod
    def _build_governance(
        source: Mapping[str, Any],
    ) -> dict[str, Any]:

        governance = source.get("governance", {})

        return {
            "status": governance.get("status"),
            "governance_id": governance.get("governance_id"),
            "execution_action": governance.get("execution_action"),
            "source_readiness_id": governance.get("source_readiness_id"),
            "source_decision_id": governance.get("source_decision_id"),
            "source_gate_id": governance.get("source_gate_id"),
            "source_certificate_id": governance.get("source_certificate_id"),
        }

    @staticmethod
    def _build_intent(
        source: Mapping[str, Any],
    ) -> dict[str, Any]:

        intent = source.get("intent", {})

        return {
            "status": intent.get("status"),
            "intent_id": intent.get("intent_id"),
            "intent_action": intent.get("intent_action"),
            "authorization_status": intent.get("authorization_status"),
            "symbol": intent.get("symbol"),
            "action": intent.get("action"),
            "quantity": intent.get("quantity"),
            "reference_price": intent.get("reference_price"),
        }

    @staticmethod
    def _build_execution(
        source: Mapping[str, Any],
    ) -> dict[str, Any]:

        execution = source.get("execution", {})

        return {
            "status": execution.get("status"),
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
        }

    @staticmethod
    def _build_reconciliation(
        source: Mapping[str, Any],
    ) -> dict[str, Any]:

        reconciliation = source.get("reconciliation", {})

        return {
            "status": reconciliation.get("status"),
            "reconciliation_id": reconciliation.get("reconciliation_id"),
            "source_execution_id": reconciliation.get("source_execution_id"),
            "quantity_reconciled": reconciliation.get("quantity_reconciled"),
            "price_reconciled": reconciliation.get("price_reconciled"),
            "value_reconciled": reconciliation.get("value_reconciled"),
            "cost_reconciled": reconciliation.get("cost_reconciled"),
            "lineage_reconciled": reconciliation.get("lineage_reconciled"),
        }

    @staticmethod
    def _build_lineage(
        source: Mapping[str, Any],
    ) -> dict[str, Any]:

        lineage = source.get("lineage", {})

        return {
            "block94": lineage.get("block94"),
            "block95": lineage.get("block95"),
            "block96": lineage.get("block96"),
            "block97": lineage.get("block97"),
            "block98": lineage.get("block98"),
            "block99": lineage.get("block99"),
            "block100": lineage.get("block100"),
            "block101": lineage.get("block101"),
        }

    @staticmethod
    def _build_safety(
        source: Mapping[str, Any],
    ) -> dict[str, Any]:

        safety = source.get("safety", {})

        return {
            "portfolio_mutation": safety.get("portfolio_mutation"),
            "valuation_mutation": safety.get("valuation_mutation"),
            "performance_mutation": safety.get("performance_mutation"),
            "risk_mutation": safety.get("risk_mutation"),
            "optimization": safety.get("optimization"),
            "order_creation": safety.get("order_creation"),
            "broker_submission": safety.get("broker_submission"),
            "live_order_submission": safety.get("live_order_submission"),
            "execution_blocked": safety.get("execution_blocked"),
            "non_mutation_invariant": safety.get("non_mutation_invariant"),
        }
