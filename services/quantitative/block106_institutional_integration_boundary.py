from __future__ import annotations

"""
EROS 3.0 - BLOCK 106
Institutional Integration Boundary

This module provides a deterministic, read-only integration boundary
between the certified EROS command-center model and future institutional
frontends.

The boundary is intentionally:

- read only
- deterministic
- auditable
- schema controlled
- lineage preserving
- broker independent
- live-execution independent
- non-mutating

Explicitly prohibited:

- broker submission
- live execution
- order creation
- portfolio mutation
- valuation mutation
- performance mutation
- risk mutation
- optimization
"""

import json
from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
from typing import Any


class EROSBlock106InstitutionalIntegrationBoundary:
    """
    Certified read-only integration boundary for EROS 3.0.

    Input:
        Certified Block 104 command-center model.

    Output:
        Deterministic institutional integration payload.

    No mutation is permitted.
    """

    BLOCK_ID = "106"
    BLOCK_NAME = "Institutional Integration Boundary"
    VERSION = "1.0"

    SAFETY_POLICY = {
        "read_only": True,
        "allow_order_creation": False,
        "allow_broker_submission": False,
        "allow_live_execution": False,
        "allow_portfolio_mutation": False,
        "allow_valuation_mutation": False,
        "allow_performance_mutation": False,
        "allow_risk_mutation": False,
        "allow_optimization": False,
        "execution_blocked": True,
        "non_mutation_invariant": True,
    }

    REQUIRED_SOURCE_FIELDS = (
        "status",
        "block_id",
        "pipeline",
        "governance",
        "intent",
        "execution",
        "reconciliation",
        "lineage",
        "safety",
    )

    def __init__(self) -> None:
        self._build_count = 0

    @staticmethod
    def _canonical_json(payload: Mapping[str, Any]) -> str:
        """
        Produce deterministic canonical JSON.
        """
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @classmethod
    def _payload_hash(cls, payload: Mapping[str, Any]) -> str:
        """
        Produce deterministic SHA-256 payload fingerprint.
        """
        canonical = cls._canonical_json(payload)
        return sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def _validate_source(
        cls,
        command_center: Mapping[str, Any],
    ) -> None:
        """
        Validate the minimum certified Block 104 source contract.
        """
        if not isinstance(command_center, Mapping):
            raise TypeError("Block 104 command-center model must be a mapping")

        missing = [field for field in cls.REQUIRED_SOURCE_FIELDS if field not in command_center]

        if missing:
            raise ValueError("Block 104 command-center model missing fields: " + ", ".join(missing))

        if str(command_center.get("block_id")) != "104":
            raise ValueError(
                "Block 106 requires certified Block 104 source; "
                f"received block_id={command_center.get('block_id')!r}"
            )

    @classmethod
    def _validate_safety(
        cls,
        source_safety: Mapping[str, Any],
    ) -> None:
        """
        Validate that the upstream command-center model remains
        non-mutating and execution-blocked.
        """
        if not isinstance(source_safety, Mapping):
            raise TypeError("Block 104 safety contract must be a mapping")

        prohibited = (
            "portfolio_mutation",
            "valuation_mutation",
            "performance_mutation",
            "risk_mutation",
            "optimization",
            "order_creation",
            "broker_submission",
            "live_order_submission",
        )

        violations = [key for key in prohibited if bool(source_safety.get(key, False))]

        if violations:
            raise ValueError(
                "Block 106 safety boundary violated by Block 104: " + ", ".join(violations)
            )

        if not bool(source_safety.get("execution_blocked", False)):
            raise ValueError("Block 106 requires execution_blocked=True")

        if not bool(source_safety.get("non_mutation_invariant", False)):
            raise ValueError("Block 106 requires non_mutation_invariant=True")

    @classmethod
    def _build_safety_contract(
        cls,
    ) -> dict[str, Any]:
        """
        Return a defensive copy of the immutable safety policy.
        """
        return deepcopy(cls.SAFETY_POLICY)

    def build_integration_payload(
        self,
        command_center: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Convert certified Block 104 command-center data into the
        Block 106 institutional integration payload.

        The returned payload is detached from the source object.
        """
        self._validate_source(command_center)

        source_safety = command_center.get("safety", {})
        self._validate_safety(source_safety)

        self._build_count += 1

        source_copy = deepcopy(dict(command_center))

        payload: dict[str, Any] = {
            "schema": {
                "name": "EROSInstitutionalIntegrationPayload",
                "version": self.VERSION,
            },
            "integration": {
                "block_id": self.BLOCK_ID,
                "block_name": self.BLOCK_NAME,
                "status": "CERTIFIED",
                "source_block_id": "104",
                "source_block_name": "EROS Command Center",
            },
            "command_center": source_copy,
            "safety": self._build_safety_contract(),
            "lineage": {
                "source_block": "104",
                "integration_block": "106",
                "source_status": str(command_center.get("status", "")),
                "source_block_id": str(command_center.get("block_id", "")),
            },
        }

        # Compute fingerprint only after the complete payload has
        # been constructed.
        payload["integrity"] = {
            "algorithm": "SHA-256",
            "payload_hash": self._payload_hash(payload),
        }

        return payload

    def build_read_only_snapshot(
        self,
        command_center: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Alias emphasizing that Block 106 provides a read-only snapshot.
        """
        return self.build_integration_payload(command_center)

    def validate_payload(
        self,
        payload: Mapping[str, Any],
    ) -> bool:
        """
        Validate a previously generated Block 106 payload.

        Validation includes both the immutable safety contract and
        the SHA-256 integrity fingerprint generated at construction.
        """
        if not isinstance(payload, Mapping):
            return False

        schema = payload.get("schema", {})
        integration = payload.get("integration", {})
        safety = payload.get("safety", {})
        command_center = payload.get("command_center")
        integrity = payload.get("integrity")

        if schema.get("name") != "EROSInstitutionalIntegrationPayload":
            return False

        if schema.get("version") != self.VERSION:
            return False

        if integration.get("block_id") != self.BLOCK_ID:
            return False

        if integration.get("source_block_id") != "104":
            return False

        if not safety.get("read_only"):
            return False

        if safety.get("allow_order_creation"):
            return False

        if safety.get("allow_broker_submission"):
            return False

        if safety.get("allow_live_execution"):
            return False

        if safety.get("allow_portfolio_mutation"):
            return False

        if safety.get("allow_valuation_mutation"):
            return False

        if safety.get("allow_performance_mutation"):
            return False

        if safety.get("allow_risk_mutation"):
            return False

        if safety.get("allow_optimization"):
            return False

        if not safety.get("execution_blocked"):
            return False

        if not safety.get("non_mutation_invariant"):
            return False

        if not isinstance(command_center, Mapping):
            return False

        # --------------------------------------------------------
        # PAYLOAD INTEGRITY
        # --------------------------------------------------------
        if not isinstance(integrity, Mapping):
            return False

        if integrity.get("algorithm") != "SHA-256":
            return False

        supplied_hash = integrity.get("payload_hash")

        if not isinstance(supplied_hash, str):
            return False

        # Reconstruct the exact pre-integrity payload used during
        # payload generation. The integrity section itself is excluded
        # from the hash calculation to avoid recursive hashing.
        unsigned_payload = {key: value for key, value in payload.items() if key != "integrity"}

        expected_hash = self._payload_hash(unsigned_payload)

        if supplied_hash != expected_hash:
            return False

        return True

    @property
    def build_count(self) -> int:
        """
        Number of payload builds performed by this instance.
        """
        return self._build_count
