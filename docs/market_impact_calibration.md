# Market-impact calibration

The calibration helper fits the same square-root impact equation used by the
bar-level execution simulator:

    observed shortfall (bps) = half spread (bps)
        + impact coefficient * volatility * sqrt(participation) * 10,000

Supply aligned series of one-way observed execution shortfall, participation
rate and decimal volatility. The estimator uses non-negative least squares
implemented for the two-parameter model without adding a dependency.

The result reports the fitted impact coefficient, half-spread estimate, sample
count, in-sample RMSE and R-squared. At least three observations and variation
in volatility-adjusted participation are required.

Use comparable observations from the same instrument, venue, order type and
timeframe. Avoid mixing buy and sell conventions or combining different market
regimes without segmentation. Estimate on a calibration period and evaluate
on a later holdout period before using the parameters in backtests. In-sample
fit is not evidence of out-of-sample execution accuracy.
