from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Mapping, Optional


BLOCK_ID = "97"
ENGINE_VERSION = "97.1.0"

STATUS_CERTIFIED = "CERTIFIED"
STATUS_BLOCKED = "BLOCKED"
STATUS_DUPLICATE = "DUPLICATE"

DECISION_ADMITTED = "ADMITTED"
DECISION_REJECTED = "REJECTED"

READINESS_READY = "READY"
READINESS_REVIEW = "REVIEW"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _hash_payload(payload: Mapping[str, Any]) -> str:
    import json

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return sha256(encoded).hexdigest().upper()


def _deepcopy(value: Any) -> Any:
    return deepcopy(value)


class EROSBlock97StressReadinessGate:
    """
    EROS 3.0 Block 97.

    Stress Decision Governance & Execution Readiness Gate.

    Consumes a CERTIFIED Block 96 stress decision and produces
    a deterministic readiness result.

    READY:
        Block 96 decision == ADMITTED.

    REVIEW:
        Block 96 decision == REJECTED.

    BLOCKED:
        Invalid, uncertified, malformed, or unsafe upstream evidence.

    This engine does not:
        - mutate portfolio state
        - mutate valuation
        - mutate performance
        - mutate risk
        - optimize
        - create orders
        - submit broker orders
        - submit live orders
    """

    def __init__(self) -> None:
        self.engine_version = ENGINE_VERSION
        self._readiness: Dict[str, Dict[str, Any]] = {}

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def certify(
        self,
        *,
        decision: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return self.evaluate(decision=decision)

    def evaluate(
        self,
        *,
        decision: Mapping[str, Any],
    ) -> Dict[str, Any]:

        validation = self._validate_decision(decision)

        if validation["status"] != STATUS_CERTIFIED:
            return validation

        source_decision = _text(
            decision.get("decision")
        )

        if source_decision == DECISION_ADMITTED:
            readiness_status = READINESS_READY
            readiness_reason = "STRESS_DECISION_ADMITTED"
        elif source_decision == DECISION_REJECTED:
            readiness_status = READINESS_REVIEW
            readiness_reason = "STRESS_POLICY_REJECTED"
        else:
            return self._blocked(
                "INVALID_DECISION"
            )

        source_decision_id = _text(
            decision.get("decision_id")
        )

        source_gate_id = _text(
            decision.get("source_gate_id")
        )

        source_certificate_id = _text(
            decision.get("source_certificate_id")
        )

        scenario_ids = [
            _text(item)
            for item in decision.get(
                "scenario_ids",
                [],
            )
        ]

        payload = {
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "source_block": "96",
            "source_decision_id": source_decision_id,
            "source_gate_id": source_gate_id,
            "source_certificate_id": source_certificate_id,
            "decision": source_decision,
            "scenario_count": int(
                decision.get("scenario_count", 0)
            ),
            "scenario_ids": scenario_ids,
            "readiness_status": readiness_status,
        }

        readiness_id = (
            "EROS97-STRESS-READINESS-"
            + _hash_payload(payload)[:20]
        )

        if readiness_id in self._readiness:
            return {
                "status": STATUS_DUPLICATE,
                "readiness_status": STATUS_DUPLICATE,
                "readiness_id": readiness_id,
            }

        result = {
            "status": STATUS_CERTIFIED,
            "readiness_status": readiness_status,
            "readiness_id": readiness_id,
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "created_at": _now_iso(),

            "source_block": "96",
            "source_decision_id": source_decision_id,
            "source_gate_id": source_gate_id,
            "source_certificate_id": source_certificate_id,

            "decision": source_decision,
            "scenario_count": int(
                decision.get("scenario_count", 0)
            ),
            "scenario_ids": scenario_ids,

            "readiness_reason": readiness_reason,

            "non_mutation_invariant": True,
            "portfolio_mutation": False,
            "valuation_mutation": False,
            "performance_mutation": False,
            "risk_mutation": False,
            "optimization": False,
            "order_creation": False,

            "broker_submission": False,
            "live_order_submission": False,
        }

        self._readiness[readiness_id] = _deepcopy(
            result
        )

        return _deepcopy(result)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def _validate_decision(
        self,
        decision: Mapping[str, Any],
    ) -> Dict[str, Any]:

        if not isinstance(
            decision,
            Mapping,
        ):
            return self._blocked(
                "MALFORMED_BLOCK_96_DECISION"
            )

        if _text(
            decision.get("status")
        ) != STATUS_CERTIFIED:
            return self._blocked(
                "SOURCE_DECISION_NOT_CERTIFIED"
            )

        if _text(
            decision.get("decision_status")
        ) != STATUS_CERTIFIED:
            return self._blocked(
                "SOURCE_DECISION_STATUS_INVALID"
            )

        if _text(
            decision.get("block_id")
        ) != "96":
            return self._blocked(
                "INVALID_SOURCE_BLOCK"
            )

        if not _text(
            decision.get("decision_id")
        ):
            return self._blocked(
                "MISSING_SOURCE_DECISION_ID"
            )

        source_block = _text(
            decision.get("source_block")
        )

        if source_block != "95":
            return self._blocked(
                "INVALID_BLOCK_95_LINEAGE"
            )

        if not _text(
            decision.get("source_gate_id")
        ):
            return self._blocked(
                "MISSING_SOURCE_GATE_ID"
            )

        if not _text(
            decision.get("source_certificate_id")
        ):
            return self._blocked(
                "MISSING_SOURCE_CERTIFICATE_ID"
            )

        source_decision = _text(
            decision.get("decision")
        )

        if source_decision not in {
            DECISION_ADMITTED,
            DECISION_REJECTED,
        }:
            return self._blocked(
                "INVALID_DECISION"
            )

        if not _text(
            decision.get("decision_reason")
        ):
            return self._blocked(
                "MISSING_DECISION_REASON"
            )

        try:
            scenario_count = int(
                decision.get(
                    "scenario_count",
                    0,
                )
            )
        except (TypeError, ValueError):
            return self._blocked(
                "INVALID_SCENARIO_COUNT"
            )

        if scenario_count < 1:
            return self._blocked(
                "INVALID_SCENARIO_COUNT"
            )

        scenario_ids = decision.get(
            "scenario_ids"
        )

        if not isinstance(
            scenario_ids,
            list,
        ):
            return self._blocked(
                "MISSING_SCENARIO_IDS"
            )

        if len(scenario_ids) != scenario_count:
            return self._blocked(
                "SCENARIO_COUNT_MISMATCH"
            )

        if any(
            not _text(item)
            for item in scenario_ids
        ):
            return self._blocked(
                "INVALID_SCENARIO_ID"
            )

        if len(set(
            _text(item)
            for item in scenario_ids
        )) != len(scenario_ids):
            return self._blocked(
                "DUPLICATE_SCENARIO_ID"
            )

        if decision.get(
            "non_mutation_invariant"
        ) is not True:
            return self._blocked(
                "NON_MUTATION_INVARIANT_FAILED"
            )

        if decision.get(
            "broker_submission"
        ) is not False:
            return self._blocked(
                "BROKER_SUBMISSION_INVARIANT_FAILED"
            )

        if decision.get(
            "live_order_submission"
        ) is not False:
            return self._blocked(
                "LIVE_EXECUTION_INVARIANT_FAILED"
            )

        return {
            "status": STATUS_CERTIFIED
        }

    # ---------------------------------------------------------
    # Blocked result
    # ---------------------------------------------------------

    def _blocked(
        self,
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "status": STATUS_BLOCKED,
            "readiness_status": STATUS_BLOCKED,
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "reason_code": reason,

            "downstream_execution_gate": STATUS_BLOCKED,

            "non_mutation_invariant": True,
            "broker_submission": False,
            "live_order_submission": False,
        }

    # ---------------------------------------------------------
    # Snapshot
    # ---------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            "engine_version": self.engine_version,
            "block_id": BLOCK_ID,
            "readiness": _deepcopy(
                self._readiness
            ),
        }


__all__ = [
    "EROSBlock97StressReadinessGate",
]
