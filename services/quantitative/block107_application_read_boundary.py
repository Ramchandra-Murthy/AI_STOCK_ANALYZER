from __future__ import annotations

"""
EROS 3.0 - BLOCK 107
Institutional Application Read Boundary

Purpose
-------
Provide a deterministic, defensive, read-only application boundary
over the certified Block 106 institutional integration payload.

Block 107 does not create orders, submit orders, communicate with
brokers, perform live execution, mutate portfolio/valuation/
performance/risk state, or perform optimization.

Flow
----
Block 104
    ->
Block 106
    ->
Block 107
    ->
Institutional Application / Dashboard / API

Safety
------
READ ONLY
NO ORDER CREATION
NO BROKER SUBMISSION
NO LIVE EXECUTION
NO MUTATION
NO OPTIMIZATION
"""

from copy import deepcopy
from typing import Any, Dict, Mapping


class EROSBlock107ApplicationReadBoundary:
    """
    Controlled read-only application boundary for EROS 3.0.
    """

    BLOCK_ID = "107"
    BLOCK_NAME = "Institutional Application Read Boundary"
    VERSION = "1.0"

    SOURCE_BLOCK_ID = "106"

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

    REQUIRED_PAYLOAD_KEYS = (
        "schema",
        "integration",
        "command_center",
        "safety",
        "lineage",
        "integrity",
    )

    @classmethod
    def _build_safety_contract(cls) -> Dict[str, Any]:
        """
        Return a defensive copy of the immutable Block 107 safety policy.
        """
        return deepcopy(cls.SAFETY_POLICY)

    @classmethod
    def _validate_safety(
        cls,
        source_safety: Mapping[str, Any],
    ) -> None:
        """
        Validate the upstream Block 106 safety contract.
        """
        if not isinstance(source_safety, Mapping):
            raise TypeError(
                "Block 106 safety contract must be a mapping"
            )

        prohibited = (
            "allow_order_creation",
            "allow_broker_submission",
            "allow_live_execution",
            "allow_portfolio_mutation",
            "allow_valuation_mutation",
            "allow_performance_mutation",
            "allow_risk_mutation",
            "allow_optimization",
        )

        violations = [
            key
            for key in prohibited
            if bool(source_safety.get(key, False))
        ]

        if violations:
            raise ValueError(
                "Block 107 safety boundary violated by Block 106: "
                + ", ".join(violations)
            )

        if not bool(source_safety.get("execution_blocked", False)):
            raise ValueError(
                "Block 107 requires execution_blocked=True"
            )

        if not bool(source_safety.get("non_mutation_invariant", False)):
            raise ValueError(
                "Block 107 requires non_mutation_invariant=True"
            )

    @classmethod
    def _validate_payload_structure(
        cls,
        payload: Mapping[str, Any],
    ) -> None:
        """
        Validate the minimum structural contract of Block 106.
        """
        if not isinstance(payload, Mapping):
            raise TypeError(
                "Block 106 payload must be a mapping"
            )

        missing = [
            key
            for key in cls.REQUIRED_PAYLOAD_KEYS
            if key not in payload
        ]

        if missing:
            raise ValueError(
                "Block 107 missing required Block 106 fields: "
                + ", ".join(missing)
            )

        schema = payload.get("schema")

        if not isinstance(schema, Mapping):
            raise TypeError(
                "Block 106 schema must be a mapping"
            )

        if schema.get("name") != "EROSInstitutionalIntegrationPayload":
            raise ValueError(
                "Invalid Block 106 schema name"
            )

        integration = payload.get("integration")

        if not isinstance(integration, Mapping):
            raise TypeError(
                "Block 106 integration must be a mapping"
            )

        if integration.get("block_id") != "106":
            raise ValueError(
                "Block 107 requires source block_id=106"
            )

        if integration.get("source_block_id") != "104":
            raise ValueError(
                "Block 107 requires Block 106 source_block_id=104"
            )

        command_center = payload.get("command_center")

        if not isinstance(command_center, Mapping):
            raise TypeError(
                "Block 106 command_center must be a mapping"
            )

        integrity = payload.get("integrity")

        if not isinstance(integrity, Mapping):
            raise TypeError(
                "Block 106 integrity must be a mapping"
            )

        if integrity.get("algorithm") != "SHA-256":
            raise ValueError(
                "Block 107 requires SHA-256 Block 106 integrity"
            )

    @classmethod
    def build_application_snapshot(
        cls,
        block106_payload: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Build a defensive, read-only application snapshot.

        The supplied Block 106 payload is never mutated.
        """
        cls._validate_payload_structure(block106_payload)

        cls._validate_safety(
            block106_payload["safety"]
        )

        snapshot = {
            "schema": {
                "name": "EROSInstitutionalApplicationReadModel",
                "version": cls.VERSION,
            },
            "application": {
                "block_id": cls.BLOCK_ID,
                "block_name": cls.BLOCK_NAME,
                "status": "CERTIFIED",
                "source_block_id": cls.SOURCE_BLOCK_ID,
                "source_block_name": (
                    "Institutional Integration Boundary"
                ),
            },
            "source_payload": deepcopy(block106_payload),
            "safety": cls._build_safety_contract(),
        }

        return snapshot

    @classmethod
    def validate_application_snapshot(
        cls,
        snapshot: Mapping[str, Any],
    ) -> bool:
        """
        Validate a previously generated application snapshot.
        """
        if not isinstance(snapshot, Mapping):
            return False

        schema = snapshot.get("schema", {})
        application = snapshot.get("application")
        source_payload = snapshot.get("source_payload")
        safety = snapshot.get("safety")

        if not isinstance(schema, Mapping):
            return False

        if schema.get("name") != (
            "EROSInstitutionalApplicationReadModel"
        ):
            return False

        if schema.get("version") != cls.VERSION:
            return False

        if not isinstance(application, Mapping):
            return False

        if application.get("block_id") != cls.BLOCK_ID:
            return False

        if application.get("source_block_id") != cls.SOURCE_BLOCK_ID:
            return False

        if application.get("status") != "CERTIFIED":
            return False

        if not isinstance(source_payload, Mapping):
            return False

        if not isinstance(safety, Mapping):
            return False

        if safety != cls.SAFETY_POLICY:
            return False

        try:
            cls._validate_payload_structure(source_payload)
            cls._validate_safety(source_payload["safety"])
        except (TypeError, ValueError):
            return False

        return True

    @classmethod
    def build_read_only_snapshot(
        cls,
        block106_payload: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Explicit read-only alias for application snapshot generation.
        """
        return cls.build_application_snapshot(
            block106_payload
        )
