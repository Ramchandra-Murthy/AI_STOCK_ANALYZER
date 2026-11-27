# Forecast Subsystem (`services/forecast`)

## Overview
The Forecast Subsystem is responsible for generating deterministic financial projections (Revenue, Net Income, Capital Expenditures, Depreciation, Working Capital, and Tax Rates) over designated multi-year horizons based on historical financial metrics.

## Architecture & Standards
- **Immutable Domain Models:** Implemented using frozen data classes with memory slot optimization.
- **Contract-Driven Design:** Clear boundaries enforced between input contracts, algorithmic processors, and output packages.
- **Serialization Ready:** Full bidirectional dictionary serialization supporting storage and API transport.

## F-10A scenario assumption input contract

`ForecastService.generate_scenario()` derives working-capital and tax assumptions
independently. A caller must provide one valid source for each assumption:

| Assumption | Preferred source | Explicit fallback |
|---|---|---|
| Working capital / revenue | `historical_working_capital` aligned to historical revenue | `working_capital_pct_revenue_assumption` |
| Tax rate | `historical_tax_rates` as decimal rates from 0 to 1 | `tax_rate_assumption` as a decimal rate from 0 to 1 |

The historical working-capital and tax inputs are independent. For example, a
caller may supply historical working capital with an explicit tax-rate fallback,
or historical tax rates with an explicit working-capital/revenue fallback.
Missing either source in a partially configured request raises a validation
error; it does not silently substitute the legacy 10% working-capital or 25%
tax defaults.

### Legacy compatibility contract

For migration compatibility only, a scenario call that omits **all four**
optional inputs (`historical_working_capital`, `historical_tax_rates`,
`tax_rate_assumption`, and
`working_capital_pct_revenue_assumption`) continues to use the pre-F-10A
legacy assumption adapter and emits a warning. This exception is intentionally
narrow: supplying any one of the four inputs opts the call into validated
F-10A derivation, where both working-capital and tax sources must be resolved.

New and migrated callers should always provide both assumption sources. The
legacy no-input path is deprecated and is retained only to avoid breaking
existing integrations during migration; it should be removed in a separately
approved breaking-change milestone after remaining callers have been migrated.

## F-10A.6 canonical projection assumption contract

`ForecastService.execute()` applies all five assumptions to the canonical
forecast package:

| Projection line | Assumption source and precedence |
|---|---|
| Revenue | Management revenue override, then `custom_growth_rate`, then the selected estimator (CAGR or regression slope / latest positive revenue) |
| EBIT | Management target EBIT margin, then `ebit_margin_assumption`, then historical EBIT margin |
| Capital expenditures | `capex_pct_revenue_assumption`, then historical mean of absolute CapEx / revenue |
| Working capital | `working_capital_pct_revenue_assumption`, then historical signed NWC / revenue |
| Tax-rate line | Historical decimal tax-rate fractions, then `tax_rate_assumption`; no generic default |

Management guidance overrides require both a source and a reason. Explicit
assumptions are validated and their source is recorded in forecast metadata.
CapEx is projected as a positive expenditure magnitude; downstream cash-flow
logic is responsible for applying the cash-outflow sign. Working capital
retains its sign, including negative NWC.

The canonical historical tax input `historical_taxes` is a series of effective
tax-rate fractions in [0, 1], not currency tax expense. Currency tax expense
must not be supplied through this field. The canonical package exposes a tax
rate, not tax expense, because this service does not calculate PBT.

The public `ForecastAssumption.ebitda_margin` field and serialized key remain
for compatibility, but the canonical forecast contract interprets this value
as EBIT margin. New code should use the `ebit_margin` property and metadata
identifies the legacy serialized field. The `ebit_margin` serialized alias is
also emitted; deserialization continues to accept older payloads containing
only `ebitda_margin`.

The precedence order is: validated management override, explicit analyst
assumption, historical-derived assumption, then an explicitly configured
statutory tax fallback where supported. The canonical execute path does not
silently substitute generic 10% working-capital or 25% tax assumptions.


### Canonical working-capital history fallback (F-10A.8)

For `ForecastService.execute()`, historical working-capital observations may
be omitted only when `working_capital_pct_revenue_assumption` is supplied
as a finite explicit ratio. In that case, projected working capital is
calculated from projected revenue multiplied by the supplied signed ratio.
Negative ratios are supported. If historical working-capital observations
are provided, they must still align with the historical-year sequence; an
explicit ratio does not excuse a malformed non-empty history. If both
historical working capital and the explicit ratio are absent, validation
fails rather than introducing a default.


### Explicit assumption independence (F-10A.10)

In the canonical `ForecastService.execute()` path, an explicit assumption may
supply its projection line when the corresponding historical observations are
unavailable:

- `ebit_margin_assumption` (or a management EBIT-margin override) permits an
  empty `historical_margins` series.
- `capex_pct_revenue_assumption` permits an empty `historical_capex` series.
- A management revenue-growth override or `custom_growth_rate` is selected
  before algorithm-derived growth is calculated, so an unnecessary regression
  estimate cannot block a valid explicit growth rate.

An explicit assumption does not excuse malformed history. Any non-empty
historical margin or CapEx series must still match `historical_years` and
contain finite values. When the relevant explicit assumption is absent, the
corresponding historical observations remain required for derivation.

The explicit CapEx/revenue ratio remains non-negative and forecasts CapEx as a
positive expenditure magnitude. Negative EBIT margins remain supported.
Working-capital fallback metadata uses the caller-independent source label
`explicit_working_capital_pct_revenue_fallback`.
