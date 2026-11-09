# Portfolio scenario stress testing

## Purpose and book relationship

This module implements a transparent scenario-analysis layer for the portfolio
risk and active portfolio management topics in *Quantitative Trading:
Algorithms, Analytics, Data Models, Optimization*, Chapter 3. Scenario
construction is an engineering workflow; the module does not claim that its
specific interface or scenarios are prescribed by the book.

## Method

- Accept a long-only, fully invested portfolio and caller-defined asset shocks.
- Calculate each asset's weighted contribution, aggregate portfolio return,
  currency P&L, stressed portfolio value, and worst contributor.
- Treat omitted asset shocks as zero so a scenario can target a subset of holdings.
- Reject unknown symbols, invalid weights, non-finite shocks, and losses below
  -100% for an asset.

## Example

```python
import pandas as pd

from algorithmic_trading.stress_testing import run_portfolio_stress_scenarios

weights = pd.Series({"RELIANCE.NS": 0.4, "HDFCBANK.NS": 0.35, "INFY.NS": 0.25})
scenarios = {
    "broad_selloff": {
        "RELIANCE.NS": -0.12,
        "HDFCBANK.NS": -0.15,
        "INFY.NS": -0.10,
    },
    "banking_shock": {"HDFCBANK.NS": -0.25},
}
report = run_portfolio_stress_scenarios(weights, scenarios, portfolio_value=1_000_000)
```

## Limitations

- Results are deterministic one-period arithmetic shocks, not forecasts,
  probabilities, VaR, expected shortfall, or multi-period paths.
- Correlation changes, volatility clustering, liquidity, market impact, taxes,
  financing, hedging, and execution timing are not inferred.
- Scenario severity and asset shocks must be selected and reviewed by the user.
- Use alongside chronological walk-forward tests and execution stress tests.
  This research tool does not authorize live orders.

## Validation

```bash
pytest tests/test_portfolio_stress_testing.py
ruff check algorithmic_trading/stress_testing.py tests/test_portfolio_stress_testing.py
black --check algorithmic_trading/stress_testing.py tests/test_portfolio_stress_testing.py
```
