# Bootstrap uncertainty for market-impact calibration

Use `bootstrap_market_impact_calibration` to quantify sampling uncertainty in
the fitted half-spread and square-root impact coefficient. The helper first
fits the original aligned observations, then resamples complete observation
triplets with replacement so realized shortfall remains paired with its
participation and volatility inputs.

The returned percentile intervals are deterministic for a fixed seed and
sample count. The default is 1,000 replicates and a 95% confidence interval.
Replicates with no predictor variation are discarded; at least 80% of the
requested replicates must remain valid. Inputs retain the calibration helper's
validation rules and require at least three observations.

These intervals describe uncertainty from the observed calibration sample;
they are not guarantees of future execution costs and do not account for
unobserved regime shifts, serial dependence, or model misspecification. Use
chronological holdout and walk-forward validation alongside these intervals.
The bootstrap is a research diagnostic and does not change live execution
parameters.
