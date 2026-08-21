from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, Mapping


class EROSBlock109InstitutionalApplicationQueryGateway:
    """
    EROS 3.0 - BLOCK 109

    Institutional Application Query Gateway.

    Purpose:
        Provide a deterministic, read-only query contract over the
        certified Block 108 application-service model.

    This boundary does not perform:
        - order creation
        - broker submission
        - live execution
        - portfolio mutation
        - valuation mutation
        - performance mutation
        - risk mutation
        - optimization
    """

    BLOCK_ID = "109"
    BLOCK_NAME = "Institutional Application Query Gateway"
    SOURCE_BLOCK = "108"
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

    QUERY_CAPABILITIES = (
        "portfolio_view",
        "valuation_view",
        "performance_view",
        "risk_view",
        "stress_view",
        "execution_governance_view",
        "evidence_view",
        "pipeline_view",
    )

    REQUIRED_SOURCE_FIELDS = (
        "schema",
        "application",
        "source",
        "safety",
    )

    def __init__(self) -> None:
        self._build_count = 0

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def build_query_model(
        self,
        *,
        application_service_model: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Build a certified read-only Block 109 query model from
        the actual Block 108 application-service contract.
        """
        self._validate_source(application_service_model)

        self._build_count += 1

        source_copy = deepcopy(
            dict(application_service_model)
        )

        model: Dict[str, Any] = {
            "schema": {
                "name": (
                    "EROSInstitutionalApplicationQueryModel"
                ),
                "version": self.VERSION,
            },
            "query": {
                "block_id": self.BLOCK_ID,
                "block_name": self.BLOCK_NAME,
                "status": "CERTIFIED",
                "source_block_id": self.SOURCE_BLOCK,
                "source_block_name": (
                    "Institutional Application "
                    "Service Boundary"
                ),
                "capabilities": list(
                    self.QUERY_CAPABILITIES
                ),
            },
            "source": source_copy,
            "safety": self._build_safety_contract(),
            "lineage": {
                "source_block": self.SOURCE_BLOCK,
                "query_block": self.BLOCK_ID,
                "source_status": str(
                    application_service_model.get(
                        "application",
                        {},
                    ).get(
                        "status",
                        "",
                    )
                ),
                "source_block_id": str(
                    application_service_model.get(
                        "application",
                        {},
                    ).get(
                        "block_id",
                        "",
                    )
                ),
            },
        }

        model["integrity"] = {
            "algorithm": "SHA-256",
            "payload_hash": self._payload_hash(
                model
            ),
        }

        return model

    def build_read_only_query_model(
        self,
        *,
        application_service_model: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Read-only alias for build_query_model().
        """
        return self.build_query_model(
            application_service_model=(
                application_service_model
            )
        )

    def validate_query_model(
        self,
        model: Mapping[str, Any],
    ) -> bool:
        """
        Validate a previously generated Block 109 query model.
        """
        if not isinstance(model, Mapping):
            return False

        schema = model.get("schema")
        query = model.get("query")
        source = model.get("source")
        safety = model.get("safety")
        lineage = model.get("lineage")
        integrity = model.get("integrity")

        if not isinstance(schema, Mapping):
            return False

        if schema.get("name") != (
            "EROSInstitutionalApplicationQueryModel"
        ):
            return False

        if schema.get("version") != self.VERSION:
            return False

        if not isinstance(query, Mapping):
            return False

        if str(query.get("block_id")) != self.BLOCK_ID:
            return False

        if query.get("status") != "CERTIFIED":
            return False

        if str(query.get("source_block_id")) != (
            self.SOURCE_BLOCK
        ):
            return False

        capabilities = query.get("capabilities")

        if not isinstance(capabilities, list):
            return False

        if set(capabilities) != set(
            self.QUERY_CAPABILITIES
        ):
            return False

        if not isinstance(source, Mapping):
            return False

        if not isinstance(safety, Mapping):
            return False

        if not self._safety_is_valid(safety):
            return False

        if not isinstance(lineage, Mapping):
            return False

        if str(lineage.get("source_block")) != (
            self.SOURCE_BLOCK
        ):
            return False

        if str(lineage.get("query_block")) != (
            self.BLOCK_ID
        ):
            return False

        if not isinstance(integrity, Mapping):
            return False

        if integrity.get("algorithm") != "SHA-256":
            return False

        supplied_hash = integrity.get(
            "payload_hash"
        )

        if not isinstance(supplied_hash, str):
            return False

        unsigned_model = {
            key: value
            for key, value in model.items()
            if key != "integrity"
        }

        expected_hash = self._payload_hash(
            unsigned_model
        )

        if supplied_hash != expected_hash:
            return False

        return True

    def snapshot(self) -> Dict[str, Any]:
        """
        Return a detached read-only gateway snapshot.
        """
        return {
            "block_id": self.BLOCK_ID,
            "block_name": self.BLOCK_NAME,
            "source_block": self.SOURCE_BLOCK,
            "version": self.VERSION,
            "build_count": self._build_count,
            "capabilities": list(
                self.QUERY_CAPABILITIES
            ),
            "safety": self._build_safety_contract(),
        }

    # ==========================================================
    # INTERNAL VALIDATION
    # ==========================================================

    @classmethod
    def _validate_source(
        cls,
        source: Mapping[str, Any],
    ) -> None:
        """
        Validate the actual Block 108 application-service
        output contract.
        """
        if not isinstance(source, Mapping):
            raise TypeError(
                "Block 108 application service model "
                "must be a mapping"
            )

        for field in cls.REQUIRED_SOURCE_FIELDS:
            if field not in source:
                raise ValueError(
                    f"BLOCK109_MISSING_{field.upper()}"
                )

        schema = source.get("schema")

        if not isinstance(schema, Mapping):
            raise ValueError(
                "BLOCK109_SCHEMA_MISSING"
            )

        if schema.get("name") != (
            "EROSInstitutionalApplicationServiceModel"
        ):
            raise ValueError(
                "BLOCK109_INVALID_SOURCE_SCHEMA"
            )

        if schema.get("version") != "1.0":
            raise ValueError(
                "BLOCK109_INVALID_SOURCE_VERSION"
            )

        application = source.get("application")

        if not isinstance(application, Mapping):
            raise ValueError(
                "BLOCK109_APPLICATION_MISSING"
            )

        if str(application.get("block_id")) != (
            cls.SOURCE_BLOCK
        ):
            raise ValueError(
                "BLOCK109_INVALID_SOURCE_BLOCK"
            )

        if application.get("status") != "CERTIFIED":
            raise ValueError(
                "BLOCK109_SOURCE_NOT_CERTIFIED"
            )

        source_payload = source.get("source")

        if not isinstance(source_payload, Mapping):
            raise ValueError(
                "BLOCK109_SOURCE_PAYLOAD_MISSING"
            )

        if str(source_payload.get("block_id")) != "107":
            raise ValueError(
                "BLOCK109_INVALID_SOURCE_LINEAGE"
            )

        if source_payload.get("status") != "CERTIFIED":
            raise ValueError(
                "BLOCK109_SOURCE_PAYLOAD_NOT_CERTIFIED"
            )

        lineage = source.get("lineage")

        if not isinstance(lineage, Mapping):
            raise ValueError(
                "BLOCK109_LINEAGE_MISSING"
            )

        if str(lineage.get("source_block")) != "107":
            raise ValueError(
                "BLOCK109_INVALID_SOURCE_LINEAGE"
            )

        if str(lineage.get("application_block")) != "108":
            raise ValueError(
                "BLOCK109_INVALID_APPLICATION_LINEAGE"
            )

        if lineage.get("source_status") != "CERTIFIED":
            raise ValueError(
                "BLOCK109_INVALID_SOURCE_STATUS"
            )

        source_lineage = lineage.get("source_lineage")

        if not isinstance(source_lineage, Mapping):
            raise ValueError(
                "BLOCK109_SOURCE_LINEAGE_MISSING"
            )

        if str(source_lineage.get("integration_block")) != "106":
            raise ValueError(
                "BLOCK109_INVALID_INTEGRATION_LINEAGE"
            )

        if str(source_lineage.get("source_block")) != "104":
            raise ValueError(
                "BLOCK109_INVALID_UPSTREAM_LINEAGE"
            )

        if str(source_lineage.get("source_block_id")) != "104":
            raise ValueError(
                "BLOCK109_INVALID_UPSTREAM_SOURCE_ID"
            )

        if source_lineage.get("source_status") != "CERTIFIED":
            raise ValueError(
                "BLOCK109_INVALID_UPSTREAM_STATUS"
            )

        source_safety = source.get("safety")

        if not isinstance(source_safety, Mapping):
            raise ValueError(
                "BLOCK109_SAFETY_MISSING"
            )

        if not cls._safety_is_valid(
            source_safety
        ):
            raise ValueError(
                "BLOCK109_UNSAFE_SOURCE"
            )

    @classmethod
    def _safety_is_valid(
        cls,
        safety: Mapping[str, Any],
    ) -> bool:
        """
        Validate the complete read-only safety contract.
        """
        if not isinstance(safety, Mapping):
            return False

        for key, expected in (
            cls.SAFETY_POLICY.items()
        ):
            if safety.get(key) is not expected:
                return False

        return True

    @classmethod
    def _build_safety_contract(
        cls,
    ) -> Dict[str, Any]:
        """
        Return a defensive copy of the immutable safety policy.
        """
        return deepcopy(
            cls.SAFETY_POLICY
        )

    @staticmethod
    def _canonical_json(
        payload: Mapping[str, Any],
    ) -> str:
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
    def _payload_hash(
        cls,
        payload: Mapping[str, Any],
    ) -> str:
        """
        Produce deterministic SHA-256 payload fingerprint.
        """
        canonical = cls._canonical_json(
            payload
        )

        return sha256(
            canonical.encode("utf-8")
        ).hexdigest()
