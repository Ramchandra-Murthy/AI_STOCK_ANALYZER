# Execution-aware backtesting

The run_execution_aware_backtest entry point connects the standalone market-impact
simulator to target-position strategy backtests without changing the existing
run_backtest API or its default results.

## Inputs and timing

- prices: bar reference prices (normally close prices).
- signals: target portfolio exposure, clipped to [-1, 1].
- volumes: traded volume for each matching bar.
- volatility: decimal volatility estimate for each matching bar.
- Signals are shifted by one bar before execution to avoid same-bar signal look-ahead.
- Target exposure is recalculated from prior marked equity; orders fill up to the
  configured maximum participation in each bar. Unfilled exposure is retried on
  later bars as the target is recalculated.

## Costs and reporting

Square-root market impact and half-spread are embedded in execution prices.
An optional IndiaEquityCostModel deducts estimated brokerage, statutory and other
configured costs separately. The result includes fills, remaining quantity,
participation, impact, execution prices, cash, shares, equity and drawdown.
The function returns the same BacktestMetrics structure as the existing backtester.

## Limitations

This is a bar-level research approximation. It treats the supplied bar price as
the reference fill price and does not model intrabar price paths, queue priority,
order-book depth, halts, auction fills, borrow availability, financing, margin
calls or broker-specific order handling. Short positions are represented
mathematically; short-sale funding and borrow costs are not modelled. Calibrate
impact coefficients by instrument and timeframe before interpreting results.
