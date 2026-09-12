from __future__ import annotations

from services.company.models import CompanyIdentity, PeriodSnapshot
from services.company.repository import InMemoryCompanyRepository
from services.company.service import CompanyKnowledgeService


def test_company_registry_and_delta_engine() -> None:
    repo = InMemoryCompanyRepository()
    service = CompanyKnowledgeService(repo)

    identity = CompanyIdentity(
        symbol="RELIANCE.NS",
        name="Reliance Industries Limited",
        sector="Energy & Retail",
        industry="Conglomerate",
    )

    service.register_company(identity)

    q1 = PeriodSnapshot(
        period="Q1-2025",
        statement_type="income",
        metrics={"revenue": 100000.0, "operating_margin": 15.0, "total_debt": 50000.0},
    )
    q2 = PeriodSnapshot(
        period="Q2-2025",
        statement_type="income",
        metrics={"revenue": 115000.0, "operating_margin": 17.5, "total_debt": 45000.0},
    )

    service.append_snapshot("RELIANCE.NS", q1)
    service.append_snapshot("RELIANCE.NS", q2)

    record = repo.get_company("RELIANCE.NS")
    assert record is not None
    assert len(record.history) == 2

    delta_report = service.compute_delta(q1, q2)
    assert delta_report["from_period"] == "Q1-2025"
    assert delta_report["to_period"] == "Q2-2025"
    assert delta_report["deltas"]["revenue"] == 15.0
    assert len(delta_report["narrative"]) > 0
