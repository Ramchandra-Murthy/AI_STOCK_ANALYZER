# Walk-forward portfolio evaluation

## Purpose and book relationship

This research evaluator operationalizes two themes in *Quantitative Trading: Algorithms, Analytics, Data Models, Optimization*:

- Chapter 2, Section 2.8.5 (page 45): in-sample and out-of-sample evaluation.
- Chapter 3, Section 3.2 (pages 67–68): transaction costs and portfolio constraints.

The book motivates the evaluation discipline and cost awareness. The specific three-strategy comparison, rolling-window schedule, and implementation are engineering choices for this repository.

## Method

At each rebalance point, only the preceding `lookback` observations are used to estimate weights. Those weights are held over the next test block, with portfolio weights drifting as assets realize returns. The process then advances to the next chronological block.

The evaluator compares:

1. `equal_weight`: equal allocation across all assets.
2. `sample_minimum_variance`: capped minimum variance using the unshrunk sample covariance estimate.
3. `shrinkage_turnover_aware`: diagonal covariance shrinkage with a quadratic penalty against changing the previous allocation.

All strategies share the same test timestamps, maximum position cap, rebalance schedule, and linear transaction-cost assumption. Initial investment is modeled as a purchase from cash. Trading costs are charged on gross traded notional (buys plus sells) at each rebalance.

## Usage

```python
from algorithmic_trading.portfolio_walk_forward import walk_forward_portfolio_evaluate

comparison = walk_forward_portfolio_evaluate(
    daily_returns,
    lookback=252,
    rebalance_every=21,
    cost_bps=15.0,
    max_weight=0.35,
)
```

The result contains one row per strategy with compounded out-of-sample return, annualized return and volatility, Sharpe ratio, maximum drawdown, cumulative gross turnover, modeled transaction costs, and the shared test period.

## Assumptions and limitations

- Input data must be complete, finite, chronological daily simple returns on a common observation grid.
- Annualization assumes 252 trading sessions.
- The proportional cost is a scenario input, not an exchange/broker fee calculation. It does not separately model taxes, spread, market impact, liquidity, or execution delay.
- This is a historical research comparison, not a forecast or guarantee. Parameter choices should be fixed before evaluating the test period; repeatedly tuning against the same out-of-sample results creates selection bias.
- No scanner signals, live allocation defaults, or broker execution paths are changed.
