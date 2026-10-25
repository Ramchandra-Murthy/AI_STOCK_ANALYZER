# Neural Networks Lab (research-only)

An isolated starting point for adapting concepts from Dmitriy Gizlyk's *Neural Networks for Algorithmic Trading with MQL5* to AI_STOCK_ANALYZER.

## Current scope

- Causal daily OHLCV feature engineering.
- A configurable future-return direction label (default five sessions).
- Chronological train/test split and scikit-learn MLP baseline.

## Safety

This is not a production trading signal. It does not fetch market data or place orders. Accuracy and ROC-AUC alone do not establish profitability. Before strategy use, add walk-forward validation, overlapping-label purging/embargo, corporate-action and survivorship checks, realistic transaction costs/slippage, and portfolio-level backtesting.
