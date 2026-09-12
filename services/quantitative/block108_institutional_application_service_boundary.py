from __future__ import annotations

"""
EROS 3.0 - BLOCK 108
Institutional Application Service Boundary

Purpose
-------
Expose a stable, read-only institutional application model derived
from the certified Block 107 application snapshot.

Safety
------
This block is strictly non-mutating.

It MUST NOT:
- create orders
- submit orders
- submit to brokers
- perform live execution
- mutate portfolio state
- mutate valuation state
- mutate performance state
- mutate risk state
- perform optimization

The block accepts only a certified Block 107 source and returns a
detached application-service model.
"""

import json
from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
from typing import Any


class EROSBlock108InstitutionalApplicationServiceBoundary:
    """Read-only institutional application service boundary."""

    BLOCK_ID = "108"
    BLOCK_NAME = "Institutional Application Service Boundary"
    SOURCE_BLOCK = "107"
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
        "schema",
        "application",
        "source_payload",
        "safety",
    )

    def __init__(self) -> None:
        self._build_count = 0

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def build_application_service_model(
        self,
        application_snapshot: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Convert a certified Block 107 application snapshot into
        a detached institutional application-service model.
        """
        self._validate_source(application_snapshot)

        source = deepcopy(dict(application_snapshot))

        self._build_count += 1

        payload: dict[str, Any] = {
            "schema": {
                "name": "EROSInstitutionalApplicationServiceModel",
                "version": self.VERSION,
            },
            "application": {
                "block_id": self.BLOCK_ID,
                "block_name": self.BLOCK_NAME,
                "status": "CERTIFIED",
            },
            "source": {
                "block_id": self.SOURCE_BLOCK,
                "block_name": "Institutional Application Read Boundary",
                "status": str(
                    source.get(
                        "application",
                        {},
                    ).get(
                        "status",
                        "",
                    )
                ),
            },
            "dashboard": deepcopy(source.get("application", {})),
            "source_payload": deepcopy(source.get("source_payload", {})),
            "lineage": {
                "source_block": self.SOURCE_BLOCK,
                "application_block": self.BLOCK_ID,
                "source_status": str(
                    source.get(
                        "application",
                        {},
                    ).get(
                        "status",
                        "",
                    )
                ),
                "source_lineage": deepcopy(source.get("source_payload", {}).get("lineage", {})),
            },
            "safety": self._build_safety_contract(),
        }

        payload["integrity"] = {
            "algorithm": "SHA-256",
            "payload_hash": self._payload_hash(payload),
        }

        return payload

    def build_read_only_application_model(
        self,
        application_snapshot: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Explicit read-only alias for the application-service model.
        """
        return self.build_application_service_model(application_snapshot)

    def validate_application_service_model(
        self,
        model: Mapping[str, Any],
    ) -> bool:
        """
        Validate a previously generated Block 108 model,
        including safety and SHA-256 integrity.
        """
        if not isinstance(model, Mapping):
            return False

        schema = model.get("schema", {})
        application = model.get("application", {})
        source = model.get("source", {})
        safety = model.get("safety", {})
        integrity = model.get("integrity")

        if schema.get("name") != ("EROSInstitutionalApplicationServiceModel"):
            return False

        if schema.get("version") != self.VERSION:
            return False

        if application.get("block_id") != self.BLOCK_ID:
            return False

        if application.get("status") != "CERTIFIED":
            return False

        if source.get("block_id") != self.SOURCE_BLOCK:
            return False

        if not self._safety_is_valid(safety):
            return False

        if not isinstance(integrity, Mapping):
            return False

        if integrity.get("algorithm") != "SHA-256":
            return False

        supplied_hash = integrity.get("payload_hash")

        if not isinstance(supplied_hash, str):
            return False

        unsigned_payload = {key: value for key, value in model.items() if key != "integrity"}

        expected_hash = self._payload_hash(unsigned_payload)

        if supplied_hash != expected_hash:
            return False

        return True

    # ==========================================================
    # VALIDATION
    # ==========================================================

    @classmethod
    def _validate_source(
        cls,
        source: Mapping[str, Any],
    ) -> None:
        """Validate the certified Block 107 source contract."""

        if not isinstance(source, Mapping):
            raise TypeError("Block 107 application snapshot must be a mapping")

        for field in cls.REQUIRED_SOURCE_FIELDS:
            if field not in source:
                raise ValueError(f"BLOCK108_MISSING_{field.upper()}")

        schema = source.get("schema")

        if not isinstance(schema, Mapping):
            raise ValueError("BLOCK108_SCHEMA_MISSING")

        if schema.get("name") != ("EROSInstitutionalApplicationReadModel"):
            raise ValueError("BLOCK108_INVALID_SOURCE_SCHEMA")

        if schema.get("version") != "1.0":
            raise ValueError("BLOCK108_INVALID_SOURCE_VERSION")

        application = source.get("application")

        if not isinstance(application, Mapping):
            raise ValueError("BLOCK108_APPLICATION_MISSING")

        if str(application.get("block_id")) != (cls.SOURCE_BLOCK):
            raise ValueError("BLOCK108_INVALID_SOURCE_BLOCK")

        if application.get("status") != "CERTIFIED":
            raise ValueError("BLOCK108_SOURCE_NOT_CERTIFIED")

        if str(application.get("source_block_id")) != "106":
            raise ValueError("BLOCK108_INVALID_SOURCE_LINEAGE")

        if not isinstance(
            source.get("source_payload"),
            Mapping,
        ):
            raise ValueError("BLOCK108_SOURCE_PAYLOAD_MISSING")

        safety = source.get("safety")

        if not isinstance(safety, Mapping):
            raise ValueError("BLOCK108_SAFETY_MISSING")

        if not cls._safety_is_valid(safety):
            raise ValueError("BLOCK108_UNSAFE_SOURCE")

    @classmethod
    def _safety_is_valid(
        cls,
        safety: Mapping[str, Any],
    ) -> bool:
        """Validate the complete read-only safety contract."""

        if not isinstance(safety, Mapping):
            return False

        for key, expected in cls.SAFETY_POLICY.items():
            if safety.get(key) is not expected:
                return False

        return True

    # ==========================================================
    # INTERNAL BUILDERS
    # ==========================================================

    @classmethod
    def _build_safety_contract(
        cls,
    ) -> dict[str, Any]:
        """Return a defensive copy of the immutable safety policy."""
        return deepcopy(cls.SAFETY_POLICY)

    @staticmethod
    def _canonical_json(
        payload: Mapping[str, Any],
    ) -> str:
        """Produce deterministic canonical JSON."""
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )

    @classmethod
    def _payload_hash(
        cls,
        payload: Mapping[str, Any],
    ) -> str:
        """Produce deterministic SHA-256 payload fingerprint."""
        canonical = cls._canonical_json(payload)

        return sha256(canonical.encode("utf-8")).hexdigest()

    # ==========================================================
    # DIAGNOSTIC SNAPSHOT
    # ==========================================================

    def snapshot(self) -> dict[str, Any]:
        """Return a detached diagnostic snapshot."""
        return {
            "block_id": self.BLOCK_ID,
            "block_name": self.BLOCK_NAME,
            "source_block": self.SOURCE_BLOCK,
            "version": self.VERSION,
            "build_count": self._build_count,
            "safety": self._build_safety_contract(),
        }
