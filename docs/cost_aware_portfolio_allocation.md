# Cost-aware portfolio allocation

## Scope and book relationship

This module extends the repository's existing portfolio-allocation foundation with diagonal covariance shrinkage, long-only capped minimum-variance weights, and an explicit quadratic penalty for changing an existing allocation. It is motivated by the book's statistical-estimation and active-portfolio-management topics (Chapters 2 and 3); it is an implementation choice, not a claim that the book specifies this exact solver.

## Method

- Estimate sample covariance from complete, chronological return observations.
- Shrink off-diagonal covariance estimates toward zero while retaining sample variances on the diagonal.
- Add a small positive ridge term for numerical conditioning.
- Minimize portfolio variance plus `turnover_penalty * ||w - w_previous||²`.
- Enforce long-only weights, full investment and a per-asset maximum weight using capped-simplex projection.
- Estimate rebalance costs from the sum of absolute target/current weight changes and a user-supplied cost in basis points.

## Example

```python
from algorithmic_trading.robust_portfolio_allocation import (
    cost_aware_minimum_variance_weights,
    estimate_rebalance_cost,
)

target = cost_aware_minimum_variance_weights(
    returns,
    previous_weights=current_weights,
    shrinkage=0.25,
    max_weight=0.35,
    turnover_penalty=0.01,
)
cost = estimate_rebalance_cost(target, current_weights, cost_bps=20.0)
```

## Assumptions and limitations

- Inputs are simple periodic returns on the same chronological observation grid. Missing or non-finite values are rejected rather than silently imputed.
- This is a long-only, fully invested optimizer. It does not estimate expected returns, short positions, leverage, taxes, market impact, liquidity constraints or execution timing.
- The turnover penalty is a smooth preference against changing weights; it is not itself a brokerage-cost forecast. The separate cost estimator is a linear scenario estimate based on user-supplied basis points.
- Covariance shrinkage reduces estimation noise but does not eliminate regime shifts or guarantee lower realized risk.
- A minimum-variance portfolio is not necessarily a return-maximizing or benchmark-beating portfolio.
- Validate weights and realized net performance in chronological walk-forward tests before any paper-trading use. This module does not authorize live orders.

## Validation

```bash
pytest tests/test_robust_portfolio_allocation.py
ruff check algorithmic_trading/robust_portfolio_allocation.py tests/test_robust_portfolio_allocation.py
black --check algorithmic_trading/robust_portfolio_allocation.py tests/test_robust_portfolio_allocation.py
```
