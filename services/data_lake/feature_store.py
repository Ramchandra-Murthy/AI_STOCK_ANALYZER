from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from services.data_lake.models import FeatureRecord

logger = logging.getLogger(__name__)

class InstitutionalFeatureStore:
    """Enterprise feature store supporting versioned financial metrics, time-travel queries, and cross-engine reuse."""

    _store: List[FeatureRecord] = []

    @classmethod
    def ingest_feature(cls, symbol: str, feature_name: str, value: float, version: str = "v1.0", metadata: Optional[Dict[str, Any]] = None) -> FeatureRecord:
        logger.info("Ingesting feature '%s' for symbol %s (Value: %.4f, Version: %s)", feature_name, symbol, value, version)
        record = FeatureRecord(
            symbol=symbol,
            feature_name=feature_name,
            value=value,
            version=version,
            metadata=metadata or {}
        )
        cls._store.append(record)
        return record

    @classmethod
    def get_feature(cls, symbol: str, feature_name: str, version: Optional[str] = None) -> Optional[float]:
        logger.info("Querying feature store for symbol %s, feature '%s' (Version: %s)", symbol, feature_name, version)
        for record in reversed(cls._store):
            if record.symbol == symbol and record.feature_name == feature_name:
                if version is None or record.version == version:
                    return record.value
        return None
