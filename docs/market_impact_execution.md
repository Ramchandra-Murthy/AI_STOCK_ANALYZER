# Volume-constrained execution and market impact

The `algorithmic_trading.market_impact` module adds an isolated, deterministic
bar-level execution simulator. It does not change the existing backtester or
India-equity statutory cost model.

## Model

For each bar, the simulator limits fills to:

`min(remaining order quantity, bar volume × maximum participation)`

One-way execution cost in basis points is estimated as:

`half_spread_bps + impact_coefficient × volatility × sqrt(fill / bar volume) × 10,000`

Volatility is a decimal return (0.02 means 2%). Buys execute above the reference
bar price; sells execute below it. Any quantity not filled by the final supplied
bar remains outstanding and is reported.

## Example

```python
import pandas as pd
from algorithmic_trading.market_impact import simulate_execution

index = pd.date_range("2026-01-01 09:15", periods=5, freq="min")
fills = simulate_execution(
    order_quantity=5_000,
    side="buy",
    prices=pd.Series([100, 100.2, 100.1, 100.4, 100.3], index=index),
    volumes=pd.Series([20_000] * 5, index=index),
    volatility=pd.Series([0.01] * 5, index=index),
    max_participation=0.10,
    half_spread_bps=2,
)
```

## Research limitations

This is a transparent approximation, not a calibrated prediction of actual
broker fills. OHLCV bars do not reveal queue position, intrabar price path,
hidden liquidity, order-book depth, auctions, circuit limits, or adverse
selection. The square-root coefficient and volatility input must be calibrated
and stress-tested for the instrument and timeframe. Do not interpret results
as live execution guarantees. Brokerage, taxes and exchange charges remain
separate and should be applied using the existing cost model.


## Order-level fill and placement diagnostics

`summarize_execution_fills` converts a `simulate_execution` fill ledger into
an order-level report when the caller supplies the order quantity, side and
arrival-price benchmark. It reports:

- filled and remaining quantity, fill ratio and completion status;
- VWAP and signed implementation shortfall versus arrival price;
- total executed notional and observed market volume;
- volume-weighted average participation and maximum bar participation;
- bars observed and the first bar by which the order was complete.

Slippage and implementation shortfall are positive when the fill is worse than
the arrival benchmark for both buys and sells. The summary excludes brokerage,
taxes and statutory charges; apply the existing India-equity cost model
separately. An incomplete order remains incomplete—do not treat the unfilled
balance as executed or silently discard it.

Example:

```python
from algorithmic_trading.market_impact import (
    simulate_execution,
    summarize_execution_fills,
)

fills = simulate_execution(...)
diagnostics = summarize_execution_fills(
    fills,
    order_quantity=5_000,
    side="buy",
    arrival_price=100.0,
)
```

The arrival price must be explicitly selected by the research caller (for
example, the decision-time mid or arrival trade price) and must use the same
instrument, currency and timestamp convention as the fill series. This remains
an OHLCV-based research estimate, not a live execution-quality report.
