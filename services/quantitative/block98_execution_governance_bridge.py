from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

BLOCK_ID = "98"
ENGINE_VERSION = "98.1.0"

STATUS_CERTIFIED = "CERTIFIED"
STATUS_BLOCKED = "BLOCKED"
STATUS_DUPLICATE = "DUPLICATE"

READINESS_READY = "READY"
READINESS_REVIEW = "REVIEW"
READINESS_BLOCKED = "BLOCKED"

GOVERNANCE_APPROVED = "APPROVED"
GOVERNANCE_REVIEW = "REVIEW"
GOVERNANCE_BLOCKED = "BLOCKED"

ACTION_EXECUTE = "EXECUTE"
ACTION_HOLD = "HOLD"
ACTION_BLOCK = "BLOCK"

GOVERNANCE_PREFIX = "EROS98-STRESS-GOVERNANCE-"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _deepcopy(value: Any) -> Any:
    return deepcopy(value)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _number(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _hash_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest().upper()


class EROSBlock98ExecutionGovernanceBridge:
    """
    EROS 3.0 Block 98.

    Converts certified Block 97 stress-readiness evidence into a
    deterministic execution-governance state.

    This block does NOT:
        - mutate portfolio state
        - mutate valuation
        - mutate performance
        - mutate risk
        - optimize
        - create orders
        - submit broker orders
        - perform live execution

    Mapping:

        READY   -> APPROVED -> EXECUTE
        REVIEW  -> REVIEW   -> HOLD
        BLOCKED -> BLOCKED  -> BLOCK
    """

    def __init__(self) -> None:
        self.block_id = BLOCK_ID
        self.engine_version = ENGINE_VERSION
        self._governance: dict[str, dict[str, Any]] = {}
        self._source_index: dict[str, str] = {}

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def certify(
        self,
        *,
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        validation = self._validate_source(decision)

        if validation["status"] != STATUS_CERTIFIED:
            return validation

        source_readiness_id = _text(decision.get("readiness_id"))

        readiness_status = _text(decision.get("readiness_status"))

        decision_value = _text(decision.get("decision"))

        governance_status, execution_action = self._map_readiness(readiness_status)

        governance_reason = self._governance_reason(
            readiness_status=readiness_status,
            decision=decision_value,
        )

        payload = {
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "source_block": "97",
            "source_readiness_id": source_readiness_id,
            "source_decision_id": _text(decision.get("source_decision_id")),
            "source_gate_id": _text(decision.get("source_gate_id")),
            "source_certificate_id": _text(decision.get("source_certificate_id")),
            "readiness_status": readiness_status,
            "decision": decision_value,
            "scenario_count": int(decision.get("scenario_count", 0)),
            "scenario_ids": list(decision.get("scenario_ids", [])),
            "governance_status": governance_status,
            "execution_action": execution_action,
            "governance_reason": governance_reason,
        }

        governance_id = f"{GOVERNANCE_PREFIX}" f"{_hash_payload(payload)[:20]}"

        if governance_id in self._governance:
            return {
                "status": STATUS_DUPLICATE,
                "governance_status": STATUS_DUPLICATE,
                "governance_id": governance_id,
                "block_id": BLOCK_ID,
                "engine_version": self.engine_version,
            }

        certificate = {
            "status": STATUS_CERTIFIED,
            "governance_status": governance_status,
            "governance_id": governance_id,
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "created_at": _now_iso(),
            "source_block": "97",
            "source_readiness_id": source_readiness_id,
            "source_decision_id": _text(decision.get("source_decision_id")),
            "source_gate_id": _text(decision.get("source_gate_id")),
            "source_certificate_id": _text(decision.get("source_certificate_id")),
            "readiness_status": readiness_status,
            "decision": decision_value,
            "scenario_count": int(decision.get("scenario_count", 0)),
            "scenario_ids": _deepcopy(decision.get("scenario_ids", [])),
            "governance": governance_status,
            "execution_action": execution_action,
            "governance_reason": governance_reason,
            "portfolio_mutation": False,
            "valuation_mutation": False,
            "performance_mutation": False,
            "risk_mutation": False,
            "optimization": False,
            "order_creation": False,
            "non_mutation_invariant": True,
            "broker_submission": False,
            "live_order_submission": False,
            "execution_blocked": True,
        }

        self._governance[governance_id] = _deepcopy(certificate)

        self._source_index[source_readiness_id] = governance_id

        return _deepcopy(certificate)

    def govern(
        self,
        *,
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.certify(decision=decision)

    def evaluate(
        self,
        *,
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.certify(decision=decision)

    def snapshot(self) -> dict[str, Any]:
        return {
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "governance": _deepcopy(self._governance),
            "source_index": _deepcopy(self._source_index),
        }

    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------

    def _validate_source(
        self,
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(decision, Mapping):
            return self._blocked("MALFORMED_READINESS")

        if _text(decision.get("status")) != STATUS_CERTIFIED:
            return self._blocked("SOURCE_STATUS_NOT_CERTIFIED")

        if _text(decision.get("readiness_status")) not in {
            READINESS_READY,
            READINESS_REVIEW,
            READINESS_BLOCKED,
        }:
            return self._blocked("INVALID_READINESS_STATUS")

        if _text(decision.get("block_id")) != "97":
            return self._blocked("INVALID_SOURCE_BLOCK")

        if _text(decision.get("source_block")) != "96":
            return self._blocked("INVALID_BLOCK_96_LINEAGE")

        if not _text(decision.get("readiness_id")):
            return self._blocked("MISSING_READINESS_ID")

        if not _text(decision.get("source_decision_id")):
            return self._blocked("MISSING_SOURCE_DECISION_ID")

        if not _text(decision.get("source_gate_id")):
            return self._blocked("MISSING_SOURCE_GATE_ID")

        if not _text(decision.get("source_certificate_id")):
            return self._blocked("MISSING_SOURCE_CERTIFICATE_ID")

        if not _text(decision.get("decision")):
            return self._blocked("MISSING_DECISION")

        scenario_count = _number(decision.get("scenario_count"))

        if scenario_count is None:
            return self._blocked("MISSING_SCENARIO_COUNT")

        if scenario_count < 1:
            return self._blocked("INVALID_SCENARIO_COUNT")

        scenario_ids = decision.get("scenario_ids")

        if not isinstance(
            scenario_ids,
            list,
        ):
            return self._blocked("MISSING_SCENARIO_IDS")

        if len(scenario_ids) != int(scenario_count):
            return self._blocked("SCENARIO_COUNT_MISMATCH")

        if not all(_text(item) for item in scenario_ids):
            return self._blocked("INVALID_SCENARIO_ID")

        if _text(decision.get("readiness_reason")) == "":
            return self._blocked("MISSING_READINESS_REASON")

        if decision.get("non_mutation_invariant") is not True:
            return self._blocked("NON_MUTATION_INVARIANT_FAILED")

        if decision.get("broker_submission") is not False:
            return self._blocked("BROKER_SUBMISSION_INVARIANT_FAILED")

        if decision.get("live_order_submission") is not False:
            return self._blocked("LIVE_EXECUTION_INVARIANT_FAILED")

        return {"status": STATUS_CERTIFIED}

    # ----------------------------------------------------------
    # Governance mapping
    # ----------------------------------------------------------

    def _map_readiness(
        self,
        readiness_status: str,
    ) -> tuple[str, str]:

        if readiness_status == READINESS_READY:
            return (
                GOVERNANCE_APPROVED,
                ACTION_EXECUTE,
            )

        if readiness_status == READINESS_REVIEW:
            return (
                GOVERNANCE_REVIEW,
                ACTION_HOLD,
            )

        return (
            GOVERNANCE_BLOCKED,
            ACTION_BLOCK,
        )

    def _governance_reason(
        self,
        *,
        readiness_status: str,
        decision: str,
    ) -> str:

        if readiness_status == READINESS_READY:
            return (
                "Block 97 readiness is READY; "
                "governance state is APPROVED and "
                "execution action is EXECUTE."
            )

        if readiness_status == READINESS_REVIEW:
            return (
                "Block 97 readiness requires REVIEW; "
                "governance state is REVIEW and "
                "execution action is HOLD."
            )

        return (
            "Block 97 readiness is BLOCKED; "
            "governance state is BLOCKED and "
            "execution action is BLOCK."
        )

    # ----------------------------------------------------------
    # Blocked response
    # ----------------------------------------------------------

    def _blocked(
        self,
        reason: str,
    ) -> dict[str, Any]:

        return {
            "status": STATUS_BLOCKED,
            "governance_status": GOVERNANCE_BLOCKED,
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "reason_code": reason,
            "execution_action": ACTION_BLOCK,
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
