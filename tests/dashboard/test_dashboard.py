from __future__ import annotations

import pytest
import os


def test_dashboard_file_exists() -> None:
    assert os.path.exists("dashboard/app.py")
    with open("dashboard/app.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert "AI Stock Analyzer" in content
    assert "ProductionDCFEngine" in content
    assert "PortfolioAnalyticsEngine" in content
