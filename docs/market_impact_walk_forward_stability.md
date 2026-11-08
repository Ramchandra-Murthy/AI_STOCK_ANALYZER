# Walk-forward market-impact stability

Use `validate_market_impact_walk_forward(observations, min_train_size=20, n_splits=5)`
to evaluate the square-root market-impact calibration across sequential
out-of-sample periods.

The input is one chronological DataFrame with a unique DatetimeIndex and
columns `observed_shortfall_bps`, `participation_rate`, and `volatility`.
The initial calibration window must contain at least three observations.
Each subsequent fold expands the calibration window, fits only on earlier
observations, and scores the next non-overlapping holdout window. Every
observation after the initial training window is scored exactly once.

At least two observations are required per holdout fold. The output includes
calibration and holdout date ranges, sample counts, fitted half-spread and
impact coefficients, RMSE, MAE, signed bias, and R-squared. Undefined
R-squared values are represented as `None`.

Compare coefficient drift and holdout errors across folds before considering
the model stable. Large parameter changes or deteriorating holdout errors can
indicate regime sensitivity or insufficient calibration data. This is a
research diagnostic only; it does not alter production execution settings or
automatically select parameters for live trading.
