from __future__ import annotations

from services.reporting.html_renderer import ReportRenderer
from services.reporting.report_builder import ResearchReportBuilder


def test_institutional_reporting_platform() -> None:
    class MockCommittee:
        consensus_signal = "BUY"
        overall_confidence = 0.91

    class MockForecast:
        expected_value = 3150.0

    report = ResearchReportBuilder.build_report("RELIANCE.NS", MockCommittee(), MockForecast())
    assert report.symbol == "RELIANCE.NS"
    assert report.recommendation == "BUY"
    assert report.metadata["version"] == "1.0.0"

    md_output = ReportRenderer.to_markdown(report)
    assert "# EROS Institutional Research Report" in md_output
    assert "RELIANCE.NS" in md_output

    html_output = ReportRenderer.to_html(report)
    assert "<html>" in html_output
    assert "RELIANCE.NS" in html_output
