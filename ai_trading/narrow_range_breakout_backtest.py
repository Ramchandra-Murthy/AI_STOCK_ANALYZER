"""Research backtest for next-bar NR4/NR7 breakouts (no order execution)."""

from __future__ import annotations

from typing import Any

import pandas as pd


def backtest_narrow_range_breakouts(
    frame: pd.DataFrame,
    *,
    lookback: int = 4,
    atr_window: int = 14,
    max_range_atr: float = 0.67,
    target_r: float = 2.0,
    risk_fraction: float = 0.01,
    initial_capital: float = 10_000.0,
    cost_bps_per_side: float = 5.0,
) -> dict[str, Any]:
    """Backtest NR4/NR7 setups using only subsequent bars.

    Entry is at the trigger, or at the next bar open when it gaps through it.
    Stop is the opposite setup boundary; target is target_r times initial risk.
    If stop and target are both touched in one bar, stop wins. Positions are
    closed at the last bar of the setup's session. Costs are charged on entry
    and exit notional using the configurable per-side basis-point estimate.
    """
    if lookback not in (4, 7):
        raise ValueError("lookback must be 4 or 7")
    if atr_window < 2 or target_r <= 0 or not 0 < risk_fraction <= 1:
        raise ValueError("invalid backtest parameters")
    if initial_capital <= 0 or cost_bps_per_side < 0:
        raise ValueError("capital must be positive and costs non-negative")
    required = {"Open", "High", "Low", "Close"}
    if frame is None or frame.empty or not required.issubset(frame.columns):
        return {"trades": [], "summary": {"trade_count": 0}}

    data = frame.copy().sort_index()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data.dropna(subset=list(required))
    if data.empty:
        return {"trades": [], "summary": {"trade_count": 0}}
    for col in required:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=list(required))
    ranges = data["High"] - data["Low"]
    previous_close = data["Close"].shift(1)
    true_range = pd.concat(
        [ranges, (data["High"] - previous_close).abs(),
         (data["Low"] - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    atr = true_range.rolling(atr_window, min_periods=atr_window).mean()
    session = pd.Series(data.index.date, index=data.index)
    trades: list[dict[str, Any]] = []
    capital = float(initial_capital)
    cost_rate = cost_bps_per_side / 10_000.0
    values = data.reset_index(drop=False)
    index_col = values.columns[0]
    values["_range"] = ranges.to_numpy()
    values["_atr"] = atr.to_numpy()
    values["_session"] = session.to_numpy()

    for i in range(max(lookback, atr_window), len(values) - 1):
        setup = values.iloc[i]
        recent = values.iloc[i - lookback + 1 : i + 1]
        setup_range = float(setup["_range"])
        setup_atr = setup["_atr"]
        if pd.isna(setup_atr) or setup_atr <= 0 or setup_range <= 0:
            continue
        if setup_range > float(recent["_range"].min()):
            continue
        if setup_range / float(setup_atr) > max_range_atr:
            continue

        nxt = values.iloc[i + 1]
        if nxt["_session"] != setup["_session"]:
            continue
        sh, sl = float(setup["High"]), float(setup["Low"])
        nh, nl, no = float(nxt["High"]), float(nxt["Low"]), float(nxt["Open"])
        long_break, short_break = nh > sh, nl < sl
        if long_break and short_break:
            continue
        if not long_break and not short_break:
            continue
        side = "LONG" if long_break else "SHORT"
        trigger = sh if long_break else sl
        entry = max(no, trigger) if long_break else min(no, trigger)
        stop = sl if long_break else sh
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        target = entry + target_r * risk if long_break else entry - target_r * risk
        risk_budget = capital * risk_fraction
        quantity = int(risk_budget // risk)
        if quantity < 1:
            continue
        session_rows = values.iloc[i + 1 :]
        session_rows = session_rows[session_rows["_session"] == setup["_session"]]
        exit_price, exit_reason, exit_idx = float(session_rows.iloc[-1]["Close"]), "SESSION_CLOSE", len(session_rows) - 1
        for j, bar in enumerate(session_rows.itertuples(index=False)):
            high = float(getattr(bar, "High"))
            low = float(getattr(bar, "Low"))
            if side == "LONG":
                stop_hit, target_hit = low <= stop, high >= target
            else:
                stop_hit, target_hit = high >= stop, low <= target
            if stop_hit:
                exit_price, exit_reason, exit_idx = stop, "STOP", j
                break
            if target_hit:
                exit_price, exit_reason, exit_idx = target, "TARGET", j
                break
        gross = (exit_price - entry) * quantity * (1 if side == "LONG" else -1)
        costs = (abs(entry * quantity) + abs(exit_price * quantity)) * cost_rate
        net = gross - costs
        capital += net
        trades.append({
            "setup_time": setup[index_col],
            "entry_time": nxt[index_col],
            "side": side,
            "pattern": f"NR{lookback}",
            "entry": entry,
            "stop": stop,
            "target": target,
            "exit": exit_price,
            "exit_reason": exit_reason,
            "quantity": quantity,
            "gross_pnl": gross,
            "costs": costs,
            "net_pnl": net,
            "r_multiple": net / (risk * quantity),
            "capital_after": capital,
        })

    pnls = [trade["net_pnl"] for trade in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    equity = pd.Series([initial_capital, *[t["capital_after"] for t in trades]])
    drawdown = equity / equity.cummax() - 1
    summary = {
        "trade_count": len(trades),
        "win_rate_pct": 100 * len(wins) / len(trades) if trades else 0.0,
        "net_pnl": sum(pnls),
        "expectancy": sum(pnls) / len(pnls) if pnls else 0.0,
        "profit_factor": sum(wins) / abs(sum(losses)) if losses else None,
        "average_r": sum(t["r_multiple"] for t in trades) / len(trades) if trades else 0.0,
        "max_drawdown_pct": 100 * float(drawdown.min()),
        "ending_capital": capital,
    }
    return {"trades": trades, "summary": summary}
