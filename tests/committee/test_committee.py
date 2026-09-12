from __future__ import annotations

from services.committee.cio import ArtificialCIO
from services.committee.models import AnalystOpinion


def test_artificial_investment_committee() -> None:
    opinions = [
        AnalystOpinion(
            department="Valuation Analyst",
            signal="BUY",
            confidence=0.93,
            score=90.0,
            strengths=["Intrinsic value exceeds market price by 28%"],
            concerns=["Valuation multiple sensitivity"],
            evidence=["DCF Model", "SOTP Model"],
            explanation="Valuation offers substantial margin of safety.",
        ),
        AnalystOpinion(
            department="Quality Analyst",
            signal="BUY",
            confidence=0.90,
            score=88.0,
            strengths=["ROIC exceeds WACC consistently"],
            concerns=["Working capital variability"],
            evidence=["ROIC Analysis", "Accrual Ratio"],
            explanation="Business converts earnings into cash efficiently.",
        ),
        AnalystOpinion(
            department="Risk Analyst",
            signal="HOLD",
            confidence=0.81,
            score=65.0,
            strengths=["Manageable debt profile"],
            concerns=["Commodity inflation risks"],
            evidence=["Altman Z-Score", "Debt/EBITDA"],
            explanation="Macro headwinds warrant cautious posture.",
        ),
    ]

    decision = ArtificialCIO.synthesize("RELIANCE.NS", opinions)

    assert decision.symbol == "RELIANCE.NS"
    assert decision.consensus_signal == "BUY"
    assert decision.overall_confidence > 0.80
    assert decision.weighted_score > 75.0
    assert len(decision.analyst_opinions) == 3
    assert "Artificial Investment Committee consensus" in decision.cio_narrative
