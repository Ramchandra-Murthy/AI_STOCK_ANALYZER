from __future__ import annotations

from services.strategy_factory.models import StrategyResult
from services.strategy_factory.strategy_engine import StrategyFactoryEngine


def test_strategy_result_immutability() -> None:
    res = StrategyResult(
        strategy_name="Buffett Compounder",
        investment_style="Quality",
        selected_candidates=["RELIANCE.NS"],
        factor_tilts={"Quality": 0.9},
        expected_cagr=0.18,
    )
    assert res.strategy_name == "Buffett Compounder"
    assert res.expected_cagr == 0.18
    assert res.timestamp is not None
    assert isinstance(res.metadata, dict)


def test_strategy_factory_engine() -> None:
    result = StrategyFactoryEngine.generate_strategy("Magic Formula Plus", "Deep Value & Quality")
    assert result.strategy_name == "Magic Formula Plus"
    assert len(result.selected_candidates) > 0
    assert "Quality" in result.factor_tilts
    assert result.expected_cagr > 0.10
