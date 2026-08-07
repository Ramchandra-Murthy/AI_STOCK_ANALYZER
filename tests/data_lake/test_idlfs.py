from __future__ import annotations

import pytest
from services.data_lake.models import FeatureRecord
from services.data_lake.feature_store import InstitutionalFeatureStore

def test_feature_record_immutability() -> None:
    rec = FeatureRecord(
        symbol="RELIANCE.NS",
        feature_name="ROIC_5Y_AVG",
        value=0.154,
        version="v1.0"
    )
    assert rec.symbol == "RELIANCE.NS"
    assert rec.feature_name == "ROIC_5Y_AVG"
    assert rec.value == 0.154
    assert rec.timestamp is not None
    assert isinstance(rec.metadata, dict)

def test_institutional_feature_store() -> None:
    InstitutionalFeatureStore.ingest_feature("RELIANCE.NS", "ROIC_5Y_AVG", 0.162, "v1.0")
    val = InstitutionalFeatureStore.get_feature("RELIANCE.NS", "ROIC_5Y_AVG", "v1.0")
    assert val == 0.162

    missing = InstitutionalFeatureStore.get_feature("TCS.NS", "NON_EXISTENT")
    assert missing is None
