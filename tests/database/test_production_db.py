from __future__ import annotations

import pytest
from backend.database.manager import ProductionDatabaseManager

def test_production_database_persistence() -> None:
    table = "valuations"
    record_id = "RELIANCE.NS-2026"
    data = {"intrinsic_value": 3520.0, "model": "Professional DCF", "margin_of_safety": 0.28}

    saved = ProductionDatabaseManager.save_record(table, record_id, data)
    assert saved["id"] == record_id
    assert saved["intrinsic_value"] == 3520.0

    retrieved = ProductionDatabaseManager.get_record(table, record_id)
    assert retrieved is not None
    assert retrieved["model"] == "Professional DCF"
    assert "updated_at" in retrieved
