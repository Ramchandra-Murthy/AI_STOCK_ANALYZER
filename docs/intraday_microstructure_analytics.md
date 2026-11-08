# Intraday Microstructure Analytics

## Purpose

This research module derives intraday volatility, range, volume-intensity and
price-impact proxies from OHLCV bars. It is designed for the Indian-equity
research workflow and can operate on one-minute or other consistently sampled
bars.

## Features

- **Realized variance / volatility:** rolling sum of squared close-to-close log
  returns and its square root.
- **Parkinson volatility:** range-based volatility estimator using each bar's
  high and low.
- **Amihud illiquidity proxy:** rolling mean of absolute log return divided by
  close-times-volume turnover.
- **Volume z-score:** current bar volume standardized against the preceding
  lookback window. The current bar is excluded from its own baseline to avoid
  look-ahead leakage.
- **Range percentage and turnover:** transparent supporting diagnostics.

## Important data limitations

OHLCV bars do not contain quoted bid/ask prices, trade direction, queue depth,
or order-level events. Consequently, these outputs must not be described as
quoted spreads, order-book imbalance, queue position, or true trade-level
market impact. Those analyses require reliable quote, trade, or Level-2 data.

The module does not fetch data, make trading decisions, alter scanner ranking,
or change live execution. It is a deterministic research feature builder.

## Usage

```python
features = intraday_microstructure_features(one_minute_bars, window=20)
latest = features.iloc[-1]
```

All rolling estimates require a complete lookback. Volatility outputs are
per-window, not annualized; the caller must account for bar frequency and
trading-session conventions before comparing different sampling intervals.

## Validation

Tests cover input validation, OHLC consistency, rolling calculations, prior-only
volume baselines, missing rows, and finite illiquidity output.
