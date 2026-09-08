from __future__ import annotations

import pandas as pd

from core.container import ServiceKey, bootstrap_container, container
from services.eros_research_service import EROSResearchService


def test_eros_container_resolves_real_application_service():
    container.clear()
    bootstrap_container()
    service = container.resolve(ServiceKey.RESEARCH)
    assert isinstance(service, EROSResearchService)


def test_eros_pipeline_reports_partial_stage_failures(monkeypatch):
    service = EROSResearchService()

    monkeypatch.setattr(
        "services.eros_research_service.get_stock_profile",
        lambda symbol: {"symbol": symbol, "price": 100.0, "eps": 5.0},
    )
    monkeypatch.setattr(
        "services.eros_research_service.get_price_history",
        lambda symbol: pd.DataFrame({"Close": [100.0], "EMA200": [90.0]}),
    )
    monkeypatch.setattr(
        "services.eros_research_service.get_ai_recommendation",
        lambda data, history: {"score": 70},
    )
    monkeypatch.setattr(
        "services.eros_research_service.get_company_news",
        lambda symbol: [],
    )
    monkeypatch.setattr(
        "services.eros_research_service.calculate_technical_score",
        lambda history: (80, ["trend"]),
    )
    monkeypatch.setattr(
        "services.eros_research_service.calculate_fundamental_score",
        lambda data: (75, ["quality"]),
    )
    monkeypatch.setattr(
        "services.eros_research_service.calculate_investment_score",
        lambda **kwargs: (77, {"Technical": 80, "Fundamental": 75}),
    )
    monkeypatch.setattr(
        "services.eros_research_service.generate_recommendation",
        lambda investment_score: {"recommendation": "BUY"},
    )
    monkeypatch.setattr(
        "services.eros_research_service.generate_trade_plan",
        lambda history, technical_score: {"status": "OK"},
    )
    monkeypatch.setattr(
        "services.eros_research_service.generate_investment_thesis",
        lambda **kwargs: {"status": "OK"},
    )
    monkeypatch.setattr(
        "services.eros_research_service.generate_scenario_analysis",
        lambda **kwargs: {"status": "OK"},
    )
    monkeypatch.setattr(
        "services.eros_research_service.generate_valuation_analysis",
        lambda **kwargs: {"status": "OK"},
    )
    monkeypatch.setattr(
        "services.eros_research_service.generate_valuation_v43",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("valuation unavailable")),
    )

    result = service.run_pipeline("reliance.ns")

    assert result["symbol"] == "RELIANCE.NS"
    assert result["investment_score"] == 77
    assert result["status"] == "PARTIAL"
    assert any(error.startswith("valuation_v43:") for error in result["errors"])
