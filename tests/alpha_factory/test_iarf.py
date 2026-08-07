from __future__ import annotations

import pytest
from services.alpha_factory.models import InvestmentOpportunity
from services.alpha_factory.screening_engine import AlphaScreeningEngine
from services.alpha_factory.ranking_engine import OpportunityRankingEngine

def test_investment_opportunity_immutability() -> None:
    opp = InvestmentOpportunity(
        symbol="RELIANCE.NS",
        thesis="Strong digital growth tailwinds.",
        expected_return=0.18,
        conviction=0.91,
        quality_score=0.92,
        valuation_score=0.88,
        momentum_score=0.75,
        catalyst_score=0.89,
        risk_score=0.25,
        priority=1
    )
    assert opp.symbol == "RELIANCE.NS"
    assert opp.priority == 1
    assert opp.timestamp is not None
    assert isinstance(opp.metadata, dict)

def test_alpha_screening_engine() -> None:
    watchlist = ["RELIANCE.NS", "SPECULATIVE.NS", "TCS.NS"]
    screened = AlphaScreeningEngine.screen_universe(watchlist)
    assert "RELIANCE.NS" in screened
    assert "TCS.NS" in screened
    assert "SPECULATIVE.NS" not in screened

def test_opportunity_ranking_engine() -> None:
    qualified = ["RELIANCE.NS", "HDFC_BANK.NS"]
    ranked = OpportunityRankingEngine.rank_opportunities(qualified)
    assert len(ranked) == 2
    assert ranked[0].priority == 1
    assert ranked[0].conviction > 0
    assert ranked[0].expected_return > 0
