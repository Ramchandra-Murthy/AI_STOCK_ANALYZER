from __future__ import annotations

import pandas as pd
import pytest

from ai_trading.strategy_regime_selector import select_regime_compatible_strategies


def _inputs():
    tournament = pd.DataFrame(
        [
            {
                "strategy": "trend_following",
                "eligible": True,
                "sharpe_ratio": 1.4,
                "max_drawdown": 0.12,
            },
            {
                "strategy": "mean_reversion",
                "eligible": True,
                "sharpe_ratio": 1.1,
                "max_drawdown": 0.08,
            },
            {
                "strategy": "short_history",
                "eligible": False,
                "sharpe_ratio": 2.0,
                "max_drawdown": 0.05,
            },
        ]
    )
    regimes = {
        "trend_following": ["BULLISH", "BEARISH"],
        "mean_reversion": ["RANGE / MIXED"],
        "short_history": ["BULLISH"],
    }
    quality = {
        "trend_following": {"status": "eligible_for_paper_trading"},
        "mean_reversion": {"status": "eligible_for_paper_trading"},
        "short_history": {"status": "eligible_for_paper_trading"},
    }
    return tournament, regimes, quality


def test_selects_only_compatible_validated_strategies():
    tournament, regimes, quality = _inputs()
    result = select_regime_compatible_strategies(
        tournament,
        regime="BULLISH",
        strategy_regimes=regimes,
        quality_results=quality,
    )
    assert result["strategy"].tolist() == ["trend_following"]
    assert result.iloc[0]["selection_scope"] == "paper_trading_only"
    assert not bool(result.iloc[0]["live_trading_authorized"])


def test_excludes_strategy_without_passing_quality_gate():
    tournament, regimes, quality = _inputs()
    quality["trend_following"] = {"status": "failed_validation"}
    result = select_regime_compatible_strategies(
        tournament,
        regime="BULLISH",
        strategy_regimes=regimes,
        quality_results=quality,
    )
    assert result.empty


def test_returns_empty_result_when_no_strategy_matches_regime():
    tournament, regimes, quality = _inputs()
    result = select_regime_compatible_strategies(
        tournament,
        regime="BEARISH",
        strategy_regimes={"mean_reversion": regimes["mean_reversion"]},
        quality_results=quality,
    )
    assert result.empty
    assert "strategy" in result.columns


def test_ranks_by_sharpe_and_limits_results():
    tournament, regimes, quality = _inputs()
    tournament.loc[tournament["strategy"] == "mean_reversion", "max_drawdown"] = 0.06
    result = select_regime_compatible_strategies(
        tournament,
        regime="RANGE / MIXED",
        strategy_regimes=regimes,
        quality_results=quality,
        top_n=1,
    )
    assert result["strategy"].tolist() == ["mean_reversion"]


@pytest.mark.parametrize("regime", ["UNKNOWN", "INSUFFICIENT DATA"])
def test_rejects_unsupported_regime(regime):
    tournament, regimes, quality = _inputs()
    with pytest.raises(ValueError, match="unsupported regime"):
        select_regime_compatible_strategies(
            tournament,
            regime=regime,
            strategy_regimes=regimes,
            quality_results=quality,
        )


def test_rejects_missing_tournament_columns():
    with pytest.raises(ValueError, match="missing required columns"):
        select_regime_compatible_strategies(
            pd.DataFrame({"strategy": ["x"]}),
            regime="BULLISH",
            strategy_regimes={},
            quality_results={},
        )
