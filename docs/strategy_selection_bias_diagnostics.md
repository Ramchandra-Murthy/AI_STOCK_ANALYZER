# Strategy-selection bias diagnostics

## Purpose

`ai_trading.strategy_selection_bias.probability_of_backtest_overfitting` estimates the Probability of Backtest Overfitting (PBO) using combinatorially symmetric cross-validation (CSCV).

This is a supplementary research diagnostic. It is not presented as a formula from *Quantitative Trading: Algorithms, Analytics, Data Models, Optimization*. It complements the book's Chapter 2 treatment of statistical models and parameter uncertainty; the CSCV/PBO method is an additional model-selection safeguard.

## Method

1. Supply a chronological DataFrame of simple periodic returns, with one column per candidate strategy/configuration.
2. Divide the observations into an even number of contiguous blocks (default 8).
3. For every combination of half the blocks, select the highest in-sample Sharpe candidate.
4. Rank that selected candidate against all candidates on the complementary blocks.
5. Convert the selected candidate's out-of-sample rank to `omega = rank / (N + 1)`, with rank 1 the worst.
6. PBO is the fraction of splits for which `logit(omega) <= 0`, i.e. the selected in-sample winner is at or below the out-of-sample median.

The function returns a summary dictionary and one row per split. Ties use average ranks; in-sample ties are resolved deterministically by input column order.

## Example

```python
summary, splits = probability_of_backtest_overfitting(
    candidate_returns,
    n_blocks=8,
    periods_per_year=252,
    risk_free_rate=0.0,
)
```

## Interpretation and limitations

- PBO is a diagnostic of selection instability across the supplied candidate set and sample; it is not the probability that a live strategy will lose money.
- The candidate strategies must be evaluated on the same chronological observations and under comparable cost and execution assumptions.
- Rows must be chronological, complete and finite. Missing values are rejected rather than silently dropped.
- Results depend on candidate-set construction, block count, return frequency, Sharpe assumptions and ties.
- CSCV splits are combinatorial rather than a chronological deployment simulation. Keep a final untouched chronological holdout and use walk-forward evaluation.
- Repeatedly changing the candidate set after inspecting PBO can itself introduce selection bias.
- A low PBO does not prove profitability, robustness to structural breaks, or suitability for live trading.

## Validation

```bash
pytest tests/test_strategy_selection_bias.py
ruff check ai_trading/strategy_selection_bias.py tests/test_strategy_selection_bias.py
black --check ai_trading/strategy_selection_bias.py tests/test_strategy_selection_bias.py
```
