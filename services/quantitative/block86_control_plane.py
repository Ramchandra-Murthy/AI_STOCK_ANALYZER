from __future__ import annotations

"""
EROS 3.0 - Block 86
Institutional Decision Control Plane.

Block 86 consumes Block 85 certification and creates a non-bypassable
control/audit decision. It does not submit orders.
"""

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Any, Dict, List, Mapping, Optional

from services.quantitative.block85_execution_certification import (
    Block85Certification,
)


ENGINE_VERSION = "EROS-3.0-BLOCK-86"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        result = value.to_dict()
        return dict(result) if isinstance(result, Mapping) else {}
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}


def _confidence(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
        if not math.isfinite(result):
            return default
        if result > 1.0:
            result /= 100.0
        return max(0.0, min(1.0, result))
    except (TypeError, ValueError):
        return default


def _hash_payload(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class Block86ControlDecision:
    decision_id: str
    symbol: str
    final_action: str
    control_state: str
    execution_allowed: bool
    confidence: float
    block85_status: str
    risk_status: str
    governance_status: str
    validation_status: str
    simulation_status: str
    rationale: List[str] = field(default_factory=list)
    blocking_reasons: List[str] = field(default_factory=list)
    audit_evidence: Dict[str, Any] = field(default_factory=dict)
    report_payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    engine_version: str = ENGINE_VERSION
    timestamp: str = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EROSBlock86ControlPlane:
    """
    Final institutional control layer.

    Invariant:
        Block 86 can preserve or further restrict Block 85 permissions,
        but it can never upgrade a blocked/review certification into EXECUTE.
    """

    ALLOWED_ACTIONS = {"BUY", "SELL", "HOLD", "REDUCE", "BLOCK", "REVIEW"}

    def __init__(
        self,
        minimum_certification_score: float = 80.0,
        minimum_confidence: float = 0.50,
    ) -> None:
        if not 0 <= minimum_certification_score <= 100:
            raise ValueError("minimum_certification_score must be 0..100")
        if not 0 <= minimum_confidence <= 1:
            raise ValueError("minimum_confidence must be 0..1")

        self.minimum_certification_score = float(minimum_certification_score)
        self.minimum_confidence = float(minimum_confidence)

    @staticmethod
    def _symbol(payload: Mapping[str, Any]) -> str:
        return str(payload.get("symbol", "")).strip().upper()

    @staticmethod
    def _status(payload: Mapping[str, Any], default: str = "UNKNOWN") -> str:
        return str(payload.get("status", payload.get("state", default))).upper()

    def evaluate(
        self,
        certification: Block85Certification | Mapping[str, Any],
        *,
        symbol: str = "",
        requested_action: str = "HOLD",
        confidence: float = 0.0,
        additional_evidence: Optional[Dict[str, Any]] = None,
    ) -> Block86ControlDecision:
        cert = _dict(certification)
        symbol = symbol.strip().upper() or self._symbol(cert)

        block85_status = str(cert.get("status", "UNKNOWN")).upper()
        risk_status = str(cert.get("risk_status", "UNKNOWN")).upper()
        governance_status = str(cert.get("governance_status", "UNKNOWN")).upper()
        validation_status = str(cert.get("validation_status", "UNKNOWN")).upper()
        simulation_status = str(cert.get("simulation_status", "UNKNOWN")).upper()

        score = float(cert.get("certification_score", 0.0) or 0.0)
        confidence_value = _confidence(confidence)

        rationale: List[str] = []
        blocking: List[str] = []

        requested_action = str(requested_action or "HOLD").upper()
        if requested_action not in self.ALLOWED_ACTIONS:
            blocking.append(f"Unsupported requested action: {requested_action}")
            requested_action = "HOLD"

        if block85_status != "CERTIFIED":
            blocking.append(
                f"Block 85 is not CERTIFIED: {block85_status}"
            )

        if not bool(cert.get("execution_allowed", False)):
            blocking.append("Block 85 execution_allowed is false")

        if score < self.minimum_certification_score:
            blocking.append(
                f"Certification score {score:.2f} is below "
                f"minimum {self.minimum_certification_score:.2f}"
            )

        if confidence_value < self.minimum_confidence:
            blocking.append(
                f"Confidence {confidence_value:.4f} is below "
                f"minimum {self.minimum_confidence:.4f}"
            )

        for name, status in (
            ("risk", risk_status),
            ("governance", governance_status),
            ("validation", validation_status),
            ("simulation", simulation_status),
        ):
            if status in {"BLOCK", "BLOCKED", "FAIL", "FAILED", "ERROR", "REJECTED"}:
                blocking.append(f"{name.title()} state is {status}")

        if blocking:
            control_state = "BLOCKED"
            final_action = "BLOCK"
            execution_allowed = False
            rationale.append(
                "Execution permission was not upgraded because Block 85 "
                "certification requirements were not satisfied."
            )
        else:
            control_state = "APPROVED"
            final_action = requested_action
            execution_allowed = requested_action in {"BUY", "SELL", "REDUCE"}
            rationale.append(
                "Block 85 certification satisfied the Block 86 control policy."
            )

        if cert.get("assumptions_detected"):
            rationale.append(
                "Explicit execution/modeling assumptions are retained in audit evidence."
            )

        evidence = {
            "block85": cert,
            "additional_evidence": additional_evidence or {},
            "broker_submission": False,
            "live_order_submission": False,
        }

        decision_payload = {
            "symbol": symbol,
            "final_action": final_action,
            "control_state": control_state,
            "execution_allowed": execution_allowed,
            "confidence": confidence_value,
            "block85_status": block85_status,
            "certification_score": score,
            "risk_status": risk_status,
            "governance_status": governance_status,
            "validation_status": validation_status,
            "simulation_status": simulation_status,
        }

        decision_id = (
            "EROS86-"
            + _hash_payload(decision_payload)[:16].upper()
        )

        audit_evidence = {
            "decision_hash": _hash_payload(decision_payload),
            "decision_id": decision_id,
            "block85_engine_version": cert.get("engine_version"),
            "block86_engine_version": ENGINE_VERSION,
            "evidence_timestamp": _utc_now(),
        }

        report_payload = {
            "symbol": symbol,
            "recommendation": final_action,
            "control_state": control_state,
            "confidence": confidence_value,
            "execution_allowed": execution_allowed,
            "certification_score": score,
            "audit_reference": decision_id,
        }

        return Block86ControlDecision(
            decision_id=decision_id,
            symbol=symbol,
            final_action=final_action,
            control_state=control_state,
            execution_allowed=execution_allowed,
            confidence=confidence_value,
            block85_status=block85_status,
            risk_status=risk_status,
            governance_status=governance_status,
            validation_status=validation_status,
            simulation_status=simulation_status,
            rationale=rationale,
            blocking_reasons=blocking,
            audit_evidence=audit_evidence,
            report_payload=report_payload,
            metadata={
                "broker_submission": False,
                "live_order_submission": False,
                "source": "EROS-3.0-BLOCK-85",
            },
        )

    def certify(
        self,
        certification: Block85Certification | Mapping[str, Any],
        **kwargs: Any,
    ) -> Block86ControlDecision:
        return self.evaluate(certification, **kwargs)


__all__ = [
    "ENGINE_VERSION",
    "Block86ControlDecision",
    "EROSBlock86ControlPlane",
]
