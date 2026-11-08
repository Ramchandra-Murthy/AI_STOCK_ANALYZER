# Out-of-sample market-impact validation

Use `validate_market_impact_out_of_sample(calibration_data, holdout_data)`
to evaluate the square-root impact model on a later, untouched period. Both
inputs are DataFrames indexed by chronological timestamps and must contain
`observed_shortfall_bps`, `participation_rate`, and `volatility`.

The calibration period must contain at least three valid observations. Its
last timestamp must be strictly earlier than the first holdout timestamp;
overlapping periods, duplicate timestamps, unsorted timestamps, invalid
participation, negative shortfall, negative volatility and non-finite values
are rejected.

The model is fitted only on calibration observations. Holdout observations
are used only to calculate predictions and diagnostics: RMSE, MAE, mean
signed error (bias), and R-squared. R-squared is undefined (`None`) when
holdout shortfall is constant. The returned predictions frame includes actual
shortfall, predicted shortfall and residuals by timestamp.

This is a chronological holdout check, not a guarantee of future execution.
For stronger evidence, repeat the evaluation across multiple non-overlapping
walk-forward periods and segment results by instrument, venue, order type,
side and timeframe. Do not activate fitted parameters in production solely
because one holdout score is favourable.
