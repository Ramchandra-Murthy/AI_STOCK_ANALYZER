from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

BLOCK_ID = "99"
ENGINE_VERSION = "EROS-3.0-BLOCK-99"

STATUS_CERTIFIED = "CERTIFIED"
STATUS_BLOCKED = "BLOCKED"
STATUS_DUPLICATE = "DUPLICATE"

GOVERNANCE_APPROVED = "APPROVED"
GOVERNANCE_REVIEW = "REVIEW"
GOVERNANCE_BLOCKED = "BLOCKED"

INTENT_AUTHORIZED = "AUTHORIZED"
INTENT_REVIEW = "REVIEW"
INTENT_BLOCKED = "BLOCKED"

ACTION_PREPARE = "PREPARE"
ACTION_HOLD = "HOLD"
ACTION_BLOCK = "BLOCK"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _number(value: Any):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _hash_payload(payload: Mapping[str, Any]) -> str:
    canonical = repr(sorted(payload.items())).encode("utf-8")
    return sha256(canonical).hexdigest().upper()


def _deepcopy(value: Any) -> Any:
    return deepcopy(value)


class EROSBlock99ExecutionIntentAuthorizationGate:
    """
    EROS 3.0 Block 99

    Block 98 governance -> deterministic execution intent.

    IMPORTANT:
        This block DOES NOT:
        - create orders
        - submit broker orders
        - execute live trades
        - mutate portfolio state
        - mutate valuation
        - mutate performance
        - mutate risk
        - perform optimization

    AUTHORIZED / PREPARE means:
        execution intent may proceed to a future control layer.

    It does NOT mean live execution.
    """

    def __init__(self) -> None:
        self.engine_version = ENGINE_VERSION
        self._intents: dict[str, dict[str, Any]] = {}
        self._source_index: dict[str, str] = {}

    def certify(
        self,
        *,
        governance: Mapping[str, Any],
    ) -> dict[str, Any]:

        validation = self._validate_source(governance)

        if validation["status"] != STATUS_CERTIFIED:
            return validation

        governance_status = _text(governance.get("governance_status"))

        intent_status, intent_action = self._map_governance(governance_status)

        intent_reason = self._intent_reason(
            governance_status=governance_status,
            execution_action=_text(governance.get("execution_action")),
        )

        payload = {
            "source_governance_id": _text(governance.get("governance_id")),
            "source_readiness_id": _text(governance.get("source_readiness_id")),
            "source_decision_id": _text(governance.get("source_decision_id")),
            "source_gate_id": _text(governance.get("source_gate_id")),
            "source_certificate_id": _text(governance.get("source_certificate_id")),
            "governance_status": governance_status,
            "execution_action": _text(governance.get("execution_action")),
            "scenario_ids": tuple(governance.get("scenario_ids", [])),
            "intent_status": intent_status,
            "intent_action": intent_action,
        }

        intent_id = "EROS99-STRESS-INTENT-" + _hash_payload(payload)[:20]

        if intent_id in self._intents:
            return {
                "status": STATUS_DUPLICATE,
                "intent_status": STATUS_DUPLICATE,
                "intent_id": intent_id,
                "block_id": BLOCK_ID,
                "engine_version": self.engine_version,
            }

        result = {
            "status": STATUS_CERTIFIED,
            "intent_status": intent_status,
            "intent_id": intent_id,
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "created_at": _now_iso(),
            # Direct Block 98 lineage
            "source_block": "98",
            "source_governance_id": _text(governance.get("governance_id")),
            "source_readiness_id": _text(governance.get("source_readiness_id")),
            "source_decision_id": _text(governance.get("source_decision_id")),
            "source_gate_id": _text(governance.get("source_gate_id")),
            "source_certificate_id": _text(governance.get("source_certificate_id")),
            # Governance evidence
            "governance_status": governance_status,
            "readiness_status": _text(governance.get("readiness_status")),
            "decision": _text(governance.get("decision")),
            "scenario_count": int(governance.get("scenario_count", 0)),
            "scenario_ids": _deepcopy(governance.get("scenario_ids", [])),
            # Intent decision
            "intent_action": intent_action,
            "intent_reason": intent_reason,
            # Safety invariants
            "portfolio_mutation": False,
            "valuation_mutation": False,
            "performance_mutation": False,
            "risk_mutation": False,
            "optimization": False,
            "order_creation": False,
            "non_mutation_invariant": True,
            "broker_submission": False,
            "live_order_submission": False,
            # Critical boundary
            "execution_blocked": True,
        }

        self._intents[intent_id] = _deepcopy(result)

        self._source_index[_text(governance.get("governance_id"))] = intent_id

        return _deepcopy(result)

    def authorize(
        self,
        *,
        governance: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.certify(governance=governance)

    def evaluate(
        self,
        *,
        governance: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.certify(governance=governance)

    def snapshot(self) -> dict[str, Any]:
        return {
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "intents": _deepcopy(self._intents),
            "source_index": _deepcopy(self._source_index),
        }

    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------

    def _validate_source(
        self,
        governance: Mapping[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(governance, Mapping):
            return self._blocked("MALFORMED_GOVERNANCE")

        if _text(governance.get("status")) != STATUS_CERTIFIED:
            return self._blocked("SOURCE_STATUS_NOT_CERTIFIED")

        if _text(governance.get("block_id")) != "98":
            return self._blocked("INVALID_SOURCE_BLOCK")

        if _text(governance.get("governance_status")) not in {
            GOVERNANCE_APPROVED,
            GOVERNANCE_REVIEW,
            GOVERNANCE_BLOCKED,
        }:
            return self._blocked("INVALID_GOVERNANCE_STATUS")

        required_text = {
            "governance_id": "MISSING_GOVERNANCE_ID",
            "source_readiness_id": "MISSING_SOURCE_READINESS_ID",
            "source_decision_id": "MISSING_SOURCE_DECISION_ID",
            "source_gate_id": "MISSING_SOURCE_GATE_ID",
            "source_certificate_id": "MISSING_SOURCE_CERTIFICATE_ID",
            "decision": "MISSING_DECISION",
            "execution_action": "MISSING_EXECUTION_ACTION",
        }

        for field, reason in required_text.items():
            if not _text(governance.get(field)):
                return self._blocked(reason)

        if _text(governance.get("source_block")) != "97":
            return self._blocked("INVALID_BLOCK_97_LINEAGE")

        if _text(governance.get("readiness_status")) not in {
            "READY",
            "REVIEW",
            "BLOCKED",
        }:
            return self._blocked("INVALID_READINESS_STATUS")

        scenario_count = _number(governance.get("scenario_count"))

        if scenario_count is None:
            return self._blocked("MISSING_SCENARIO_COUNT")

        if scenario_count < 1:
            return self._blocked("INVALID_SCENARIO_COUNT")

        scenario_ids = governance.get("scenario_ids")

        if not isinstance(scenario_ids, list):
            return self._blocked("MISSING_SCENARIO_IDS")

        if len(scenario_ids) != int(scenario_count):
            return self._blocked("SCENARIO_COUNT_MISMATCH")

        if not all(_text(item) for item in scenario_ids):
            return self._blocked("INVALID_SCENARIO_ID")

        if governance.get("non_mutation_invariant") is not True:
            return self._blocked("NON_MUTATION_INVARIANT_FAILED")

        boolean_false_fields = {
            "portfolio_mutation": "PORTFOLIO_MUTATION_INVARIANT_FAILED",
            "valuation_mutation": "VALUATION_MUTATION_INVARIANT_FAILED",
            "performance_mutation": "PERFORMANCE_MUTATION_INVARIANT_FAILED",
            "risk_mutation": "RISK_MUTATION_INVARIANT_FAILED",
            "optimization": "OPTIMIZATION_INVARIANT_FAILED",
            "order_creation": "ORDER_CREATION_INVARIANT_FAILED",
            "broker_submission": "BROKER_SUBMISSION_INVARIANT_FAILED",
            "live_order_submission": "LIVE_EXECUTION_INVARIANT_FAILED",
        }

        for field, reason in boolean_false_fields.items():
            if governance.get(field) is not False:
                return self._blocked(reason)

        if governance.get("execution_blocked") is not True:
            return self._blocked("EXECUTION_BLOCKING_INVARIANT_FAILED")

        return {"status": STATUS_CERTIFIED}

    # ----------------------------------------------------------
    # Governance -> Intent mapping
    # ----------------------------------------------------------

    def _map_governance(
        self,
        governance_status: str,
    ) -> tuple[str, str]:

        if governance_status == GOVERNANCE_APPROVED:
            return (
                INTENT_AUTHORIZED,
                ACTION_PREPARE,
            )

        if governance_status == GOVERNANCE_REVIEW:
            return (
                INTENT_REVIEW,
                ACTION_HOLD,
            )

        return (
            INTENT_BLOCKED,
            ACTION_BLOCK,
        )

    def _intent_reason(
        self,
        *,
        governance_status: str,
        execution_action: str,
    ) -> str:

        if governance_status == GOVERNANCE_APPROVED:
            return (
                "Block 98 governance is APPROVED; "
                "execution intent is AUTHORIZED for "
                "PREPARE only. Live execution remains blocked."
            )

        if governance_status == GOVERNANCE_REVIEW:
            return "Block 98 governance requires REVIEW; " "execution intent is held."

        return "Block 98 governance is BLOCKED; " "execution intent is blocked."

    # ----------------------------------------------------------
    # Blocked response
    # ----------------------------------------------------------

    def _blocked(
        self,
        reason: str,
    ) -> dict[str, Any]:

        return {
            "status": STATUS_BLOCKED,
            "intent_status": INTENT_BLOCKED,
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "reason_code": reason,
            "intent_action": ACTION_BLOCK,
            "execution_blocked": True,
            "portfolio_mutation": False,
            "valuation_mutation": False,
            "performance_mutation": False,
            "risk_mutation": False,
            "optimization": False,
            "order_creation": False,
            "non_mutation_invariant": True,
            "broker_submission": False,
            "live_order_submission": False,
        }
