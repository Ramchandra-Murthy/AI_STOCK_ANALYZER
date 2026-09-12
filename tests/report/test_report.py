from __future__ import annotations

from services.report.engine import ProductionReportEngine


def test_production_report_generation() -> None:
    engine = ProductionReportEngine()
    result = engine.generate(
        "RELIANCE.NS",
        format_type="MULTI-FORMAT",
        analysis_data={"recommendation": "BUY", "composite_score": 82.0},
    )

    assert result.symbol == "RELIANCE.NS"
    assert result.file_path != ""
    assert "RELIANCE.NS" in result.content
    assert result.metadata["status"] == "generated"
