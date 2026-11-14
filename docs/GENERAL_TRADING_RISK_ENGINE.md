# General Trading Profiles and Risk Engine

The trading profile and risk engine are reusable account-level components. They
do not assume a fixed capital amount, fixed rupee loss, holding period, exchange,
or strategy. Create separate `TradingProfile` instances for intraday, swing,
positional, or long-term workflows.

## Configuration

`TradingProfile` captures capital, percentage or fixed-currency per-trade
risk, daily loss limit, maximum position and portfolio exposure, cash reserve,
maximum positions, timeframe, exchange, stop methodology, short-selling
permission, and an estimated round-trip cost rate.

The supplied defaults are examples only. Applications should load user-selected
profiles from validated configuration storage and display the active profile.

## Position planning

`calculate_position_plan` combines:
- per-trade risk budget;
- distance between entry and stop;
- estimated round-trip costs;
- available cash after the reserve;
- maximum position notional;
- remaining portfolio exposure; and
- remaining daily loss allowance.

The final quantity is the minimum allowed by risk and capital constraints.
Invalid stop direction is rejected. Short positions require explicit profile
permission.

## Important limitations

The cost estimate is an approximation, not a broker fee calculator. Stop
execution can exceed the estimate due to gaps, slippage, liquidity, and market
impact. This module plans positions; it does not submit broker orders, fetch
market data, or guarantee a maximum realized loss.

## Example

```python
from algorithmic_trading.trading_profile import TradingProfile
from algorithmic_trading.risk_engine import calculate_position_plan

profile = TradingProfile(
    name="swing-growth",
    style="swing",
    capital=250_000,
    risk_mode="percent",
    risk_value=0.75,
    max_daily_loss_pct=2.0,
)
plan = calculate_position_plan(
    profile, entry_price=500, stop_price=485, side="LONG"
)
```
