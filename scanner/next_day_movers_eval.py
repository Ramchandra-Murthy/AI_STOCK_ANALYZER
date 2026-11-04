"""Walk-forward evaluation of the next-business-day ranking score (research only).

For every historical date ``t`` the evaluation rebuilds the cross-section exactly as the
live scanner would at the close of ``t`` (same cleaning, same ``compute_feature_frame``,
same eligibility filters, same ``score_panel``) and then looks one *market* session ahead
to ``t+1`` for the outcome. Features never see ``t+1``; outcomes are never used to build
features or choose weights (weights are fixed a priori, so nothing is fitted and the
sequential folds measure stability over time rather than tuning).

Outcomes
--------
* Primary, tradable-in-principle: next-session **open -> close** (a scan finished after the
  close of ``t`` cannot buy at the close of ``t``). Transaction costs and slippage are
  deducted for a same-day round trip.
* Secondary, descriptive: next-session **close -> close** (the "moved upward" definition),
  gross of costs, because it is not obtainable after the cutoff.

Nothing here proves a live edge. Read ``WalkForwardResult.limitations`` before using any
number: the universe is today's curated list (survivorship), data is delayed Yahoo history,
and fills at the official open are idealised.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from algorithmic_trading.trading_costs import IndiaEquityCostModel
from algorithmic_trading.walk_forward_validation import benchmark_relative_metrics
from scanner.next_day_movers import (
    DISCLAIMER,
    FrameFetcher,
    Instrument,
    ScannerConfig,
    add_relative_strength,
    benchmark_feature_frame,
    benchmark_tickers,
    build_universe,
    clean_ohlcv_history,
    compute_feature_frame,
    default_frame_fetcher,
    ineligibility_flags,
    rankable,
    score_panel,
    sector_of,
    ticker_for,
)

TRADING_DAYS_PER_YEAR = 252
OUTCOME_COLUMNS = ("o2c", "c2c")

LIMITATIONS: tuple[str, ...] = (
    "Survivorship/selection bias: the universe is today's curated list of liquid names; "
    "delisted, suspended-for-years or dropped stocks are absent, which flatters results.",
    "Data is delayed, auto-adjusted Yahoo Finance history that can be revised or contain gaps "
    "and bad ticks; it is not an exchange-grade point-in-time database.",
    "Fills at the official next open are idealised: no auction impact, partial fills, rejected "
    "orders or circuit-limit lock-ins. Costs/slippage use approximate, configurable rates.",
    "Weights were fixed a priori but chosen from common factor knowledge, and one "
    "configuration was evaluated; any later tuning on these results would be data snooping.",
    "Historical NSE surveillance flags, delivery data, news and corporate actions are not "
    "available point-in-time, so the backtest evaluates the score only, not those live filters.",
    "Equal-weight daily rebalancing ignores capacity and market impact; the sample covers a "
    "single market regime, so out-of-sample here is not out-of-regime.",
    "Hit rates near the base rate (about half of stocks rise on a typical day) mean no skill; "
    "always compare precision with the base rate and net returns with the baselines.",
)


def default_intraday_cost_model() -> IndiaEquityCostModel:
    """Approximate, configurable same-day equity round-trip costs.

    These are illustrative defaults, not a live statutory rate feed; statutory charges and
    broker pricing change, so verify them for the broker and date under test.
    """
    return IndiaEquityCostModel(
        brokerage_bps=1.0,
        exchange_transaction_bps=0.3,
        regulatory_bps=0.01,
        stt_sell_bps=2.5,
        stamp_duty_buy_bps=0.3,
        slippage_bps=5.0,
    )


def round_trip_cost_fraction(model: IndiaEquityCostModel) -> float:
    """Cost of buying and selling one unit of notional once each, as a fraction."""
    return float(model.cost_fraction(pd.Series([1.0]), pd.Series([1.0])).iloc[0])


@dataclass(frozen=True)
class EvalConfig:
    """Evaluation settings. ``scanner`` supplies the same filters the live scan uses."""

    top_k: int = 10
    n_splits: int = 5
    cost_model: IndiaEquityCostModel = field(default_factory=default_intraday_cost_model)
    scanner: ScannerConfig = field(default_factory=ScannerConfig)
    bootstrap_samples: int = 2000
    bootstrap_block: int = 5
    seed: int = 7
    min_eval_days: int = 120
    min_positive_fold_share: float = 0.6

    def __post_init__(self) -> None:
        if self.top_k < 1:
            raise ValueError("top_k must be at least 1")
        if self.n_splits < 1:
            raise ValueError("n_splits must be at least 1")
        if self.bootstrap_block < 1 or self.bootstrap_samples < 100:
            raise ValueError("bootstrap_block must be >=1 and bootstrap_samples >=100")


class EvaluationDataError(RuntimeError):
    """Raised when historical data needed for the evaluation cannot be obtained."""


@dataclass(frozen=True)
class WalkForwardResult:
    """Evaluation output; every table is plain pandas for display and testing."""

    summary: pd.DataFrame
    folds: pd.DataFrame
    quintiles: pd.DataFrame
    daily: pd.DataFrame
    coverage: dict[str, Any]
    assessment: dict[str, Any]
    round_trip_cost_bps: float
    limitations: tuple[str, ...] = LIMITATIONS
    disclaimer: str = DISCLAIMER


# ---------------------------------------------------------------------------
# Panel construction (features at t, outcomes at the next market session)
# ---------------------------------------------------------------------------


def build_evaluation_panel(
    frames: Mapping[str, pd.DataFrame],
    instruments: Mapping[str, Instrument],
    benchmarks: Mapping[str, pd.DataFrame],
    scanner: ScannerConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    """Return ``(panel, index_outcomes, dropped)``.

    ``panel`` is indexed by ``(date, ticker)``; feature columns use data up to ``date``
    only, while ``o2c``/``c2c`` look at the next market session. ``index_outcomes`` holds
    the primary benchmark's outcomes on the same ``date`` index.
    """
    cleaned: dict[str, pd.DataFrame] = {}
    unreliable_by_ticker: dict[str, pd.Series] = {}
    dropped: dict[str, list[str]] = {}
    for ticker, frame in frames.items():
        if ticker not in instruments:
            continue
        clean, unreliable, reasons = clean_ohlcv_history(frame)
        if clean is None or unreliable is None:
            dropped[ticker] = reasons
        else:
            cleaned[ticker] = clean
            unreliable_by_ticker[ticker] = unreliable
    if not cleaned:
        raise EvaluationDataError("no usable price history for any symbol")

    calendar = pd.DatetimeIndex(sorted(set().union(*(c.index for c in cleaned.values()))))

    bm_clean: dict[str, pd.DataFrame] = {}
    for exchange, frame in benchmarks.items():
        clean, _, _ = clean_ohlcv_history(frame)
        if clean is not None:
            bm_clean[exchange] = clean
    bm_features = {ex: benchmark_feature_frame(c) for ex, c in bm_clean.items()}

    parts: list[pd.DataFrame] = []
    for ticker, clean in cleaned.items():
        inst = instruments[ticker]
        feats = compute_feature_frame(clean)
        feats["eligible"] = ~ineligibility_flags(feats, scanner).any(axis=1) & ~(
            unreliable_by_ticker[ticker].reindex(feats.index).fillna(False).astype(bool)
        )
        next_open = clean["Open"].reindex(calendar).shift(-1).reindex(feats.index)
        next_close = clean["Close"].reindex(calendar).shift(-1).reindex(feats.index)
        feats["o2c"] = next_close / next_open - 1.0
        feats["c2c"] = next_close / feats["close"] - 1.0
        if inst.exchange in bm_features:
            feats = feats.join(bm_features[inst.exchange], how="left")
        else:
            feats["bm_ret_5d"] = np.nan
            feats["bm_ret_20d"] = np.nan
        feats["sector"] = sector_of(inst)
        feats["exchange"] = inst.exchange
        feats["ticker"] = ticker
        feats.index.name = "date"
        parts.append(feats.reset_index())

    panel = pd.concat(parts, ignore_index=True).set_index(["date", "ticker"]).sort_index()

    primary = next((ex for ex in ("NSE", "BSE") if ex in bm_clean), None)
    index_outcomes = pd.DataFrame(index=calendar, columns=list(OUTCOME_COLUMNS), dtype=float)
    if primary is not None:
        idx = bm_clean[primary]
        nxt_open = idx["Open"].reindex(calendar).shift(-1)
        nxt_close = idx["Close"].reindex(calendar).shift(-1)
        index_outcomes["o2c"] = nxt_close / nxt_open - 1.0
        index_outcomes["c2c"] = nxt_close / idx["Close"].reindex(calendar) - 1.0
    return panel, index_outcomes, dropped


def _clean_mean(values: pd.Series) -> float:
    valid = values.dropna()
    return float(valid.mean()) if len(valid) else float("nan")


def _top_k(scores: pd.Series, k: int, tie_break: pd.Index) -> pd.Index:
    """Highest ``k`` values; ties broken by ticker so results are deterministic."""
    frame = pd.DataFrame({"v": scores, "t": tie_break})
    return frame.sort_values(["v", "t"], ascending=[False, True]).head(k).index


def run_daily_selection(panel: pd.DataFrame, index_outcomes: pd.DataFrame, config: EvalConfig):
    """Walk through dates, rank, pick top-k and record next-session outcomes."""
    scanner = config.scanner
    min_names = max(config.top_k, scanner.min_cross_section)
    records: list[dict[str, Any]] = []
    quintile_rows: list[dict[str, Any]] = []
    skipped = {"too_few_eligible": 0, "too_few_ranked": 0, "no_valid_outcomes": 0}
    eligible_counts: list[int] = []

    for date, day in panel.groupby(level="date", sort=True):
        day = day.droplevel("date")
        if not day[list(OUTCOME_COLUMNS)].notna().any().any():
            continue  # final bar: no next session yet
        eligible = day[day["eligible"]]
        if len(eligible) < scanner.min_cross_section:
            skipped["too_few_eligible"] += 1
            continue
        eligible = add_relative_strength(eligible)
        scores, _ = score_panel(eligible, scanner)
        ranked = rankable(scores, scanner)
        if len(ranked) < min_names:
            skipped["too_few_ranked"] += 1
            continue

        eligible_counts.append(len(eligible))
        score_picks = _top_k(ranked["score"], config.top_k, ranked.index.to_series())
        mom_pool = eligible.index.to_series()
        mom_picks = _top_k(eligible["ret_5d"], config.top_k, mom_pool)
        picked = eligible.loc[score_picks]
        if picked["o2c"].notna().sum() == 0:
            skipped["no_valid_outcomes"] += 1
            continue
        momentum = eligible.loc[mom_picks]

        record: dict[str, Any] = {
            "date": date,
            "n_eligible": len(eligible),
            "n_ranked": len(ranked),
        }
        for label, group in (("score", picked), ("mom5", momentum), ("universe", eligible)):
            for outcome in OUTCOME_COLUMNS:
                valid = group[outcome].dropna()
                record[f"{label}_{outcome}"] = float(valid.mean()) if len(valid) else float("nan")
                record[f"{label}_{outcome}_valid"] = len(valid)
                record[f"{label}_{outcome}_pos"] = int((valid > 0).sum())
        record["score_picks"] = ",".join(str(t) for t in score_picks)
        record["index_o2c"] = float(index_outcomes["o2c"].get(date, np.nan))
        record["index_c2c"] = float(index_outcomes["c2c"].get(date, np.nan))
        records.append(record)

        quintile = np.ceil(ranked["score"].rank(pct=True, method="first") * 5).clip(1, 5)
        joined = eligible.loc[ranked.index, list(OUTCOME_COLUMNS)].assign(quintile=quintile)
        for q, grp in joined.groupby("quintile"):
            quintile_rows.append(
                {
                    "date": date,
                    "quintile": int(q),
                    "o2c": _clean_mean(grp["o2c"]),
                    "c2c": _clean_mean(grp["c2c"]),
                    "pos_o2c": int((grp["o2c"] > 0).sum()),
                    "valid_o2c": int(grp["o2c"].notna().sum()),
                }
            )

    daily = pd.DataFrame(records).set_index("date") if records else pd.DataFrame()
    quintiles = pd.DataFrame(quintile_rows)
    return daily, quintiles, skipped, eligible_counts


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def _max_drawdown(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return float("nan")
    wealth = (1.0 + clean).cumprod()
    return float((wealth / wealth.cummax() - 1.0).min())


def block_bootstrap_ci(
    values: np.ndarray, *, block: int, samples: int, seed: int, alpha: float = 0.05
) -> tuple[float, float]:
    """Moving-block bootstrap interval for the mean (keeps short-range autocorrelation)."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 2 * block:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    n_blocks = math.ceil(n / block)
    starts = rng.integers(0, n - block + 1, size=(samples, n_blocks))
    index = (starts[:, :, None] + np.arange(block)).reshape(samples, -1)[:, :n]
    means = x[index].mean(axis=1)
    low, high = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(low), float(high)


def _series_row(name: str, returns: pd.Series, benchmark: pd.Series) -> dict[str, Any]:
    r = returns.dropna()
    row: dict[str, Any] = {
        "series": name,
        "days": len(r),
        "mean_bps": float(r.mean() * 1e4) if len(r) else float("nan"),
        "median_bps": float(r.median() * 1e4) if len(r) else float("nan"),
        "day_hit_rate": float((r > 0).mean()) if len(r) else float("nan"),
        "cumulative_return": float((1.0 + r).prod() - 1.0) if len(r) else float("nan"),
        "max_drawdown": _max_drawdown(r),
        "sharpe_indicative": (
            float(r.mean() / r.std(ddof=1) * math.sqrt(TRADING_DAYS_PER_YEAR))
            if len(r) > 1 and r.std(ddof=1) > 0
            else float("nan")
        ),
    }
    aligned = pd.concat([r.rename("s"), benchmark.rename("b")], axis=1).dropna()
    if len(aligned) > 1:
        rel = benchmark_relative_metrics(aligned["s"], aligned["b"])
        row["mean_excess_vs_index_bps"] = float((aligned["s"] - aligned["b"]).mean() * 1e4)
        row["information_ratio"] = float(rel["information_ratio"])
        row["cumulative_excess_vs_index"] = float(rel["cumulative_excess_return"])
    else:
        row["mean_excess_vs_index_bps"] = float("nan")
        row["information_ratio"] = float("nan")
        row["cumulative_excess_vs_index"] = float("nan")
    return row


def _pooled_precision(daily: pd.DataFrame, label: str, outcome: str) -> float:
    positives = daily[f"{label}_{outcome}_pos"].sum()
    valid = daily[f"{label}_{outcome}_valid"].sum()
    return float(positives / valid) if valid else float("nan")


def summarise(daily: pd.DataFrame, config: EvalConfig) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build the comparison table and the pre-registered edge assessment."""
    cost = round_trip_cost_fraction(config.cost_model)
    series = {
        "Score top-k, net of costs (open->close)": daily["score_o2c"] - cost,
        "Score top-k, gross (open->close)": daily["score_o2c"],
        "Momentum-5d top-k, net of costs (open->close)": daily["mom5_o2c"] - cost,
        "Equal-weight eligible universe, gross (open->close)": daily["universe_o2c"],
        "Index, gross (open->close)": daily["index_o2c"],
        "Score top-k, gross (close->close, not tradable after cutoff)": daily["score_c2c"],
        "Equal-weight eligible universe, gross (close->close)": daily["universe_c2c"],
        "Index, gross (close->close)": daily["index_c2c"],
    }
    rows = []
    for name, returns in series.items():
        benchmark = daily["index_c2c"] if "close->close" in name else daily["index_o2c"]
        rows.append(_series_row(name, returns, benchmark))
    summary = pd.DataFrame(rows).set_index("series")

    precision = {
        "Score top-k precision (open->close, gross)": _pooled_precision(daily, "score", "o2c"),
        "Momentum-5d top-k precision (open->close, gross)": _pooled_precision(daily, "mom5", "o2c"),
        "Universe base rate (open->close, gross)": _pooled_precision(daily, "universe", "o2c"),
        "Score top-k precision (close->close)": _pooled_precision(daily, "score", "c2c"),
        "Universe base rate (close->close)": _pooled_precision(daily, "universe", "c2c"),
    }

    excess = (daily["score_o2c"] - cost - daily["universe_o2c"]).dropna().to_numpy()
    excess_mom = (daily["score_o2c"] - daily["mom5_o2c"]).dropna().to_numpy()
    low, high = block_bootstrap_ci(
        excess, block=config.bootstrap_block, samples=config.bootstrap_samples, seed=config.seed
    )
    low_m, high_m = block_bootstrap_ci(
        excess_mom, block=config.bootstrap_block, samples=config.bootstrap_samples, seed=config.seed
    )
    net_mean = float((daily["score_o2c"] - cost).mean())
    return summary, {
        "precision": precision,
        "mean_net_excess_vs_universe_bps": (
            float(excess.mean() * 1e4) if len(excess) else float("nan")
        ),
        "net_excess_vs_universe_ci95_bps": (low * 1e4, high * 1e4),
        "gross_excess_vs_momentum5_ci95_bps": (low_m * 1e4, high_m * 1e4),
        "mean_net_return_bps": net_mean * 1e4,
        "bootstrap": f"moving-block, block={config.bootstrap_block}, samples={config.bootstrap_samples}",
    }


def build_folds(daily: pd.DataFrame, config: EvalConfig) -> pd.DataFrame:
    """Sequential, non-overlapping chronological folds of the evaluated dates."""
    cost = round_trip_cost_fraction(config.cost_model)
    n = len(daily)
    n_splits = min(config.n_splits, max(1, n // 2))
    edges = np.linspace(0, n, n_splits + 1).astype(int)
    rows = []
    for fold, (start, stop) in enumerate(zip(edges[:-1], edges[1:], strict=True), start=1):
        chunk = daily.iloc[start:stop]
        if chunk.empty:
            continue
        net = chunk["score_o2c"] - cost
        rows.append(
            {
                "fold": fold,
                "start": chunk.index[0].date().isoformat(),
                "end": chunk.index[-1].date().isoformat(),
                "days": len(chunk),
                "net_mean_bps": float(net.mean() * 1e4),
                "net_excess_vs_universe_bps": float((net - chunk["universe_o2c"]).mean() * 1e4),
                "net_excess_vs_index_bps": float((net - chunk["index_o2c"]).mean() * 1e4),
                "precision_gross": _pooled_precision(chunk, "score", "o2c"),
                "base_rate": _pooled_precision(chunk, "universe", "o2c"),
                "net_cumulative_return": float((1.0 + net).prod() - 1.0),
                "max_drawdown": _max_drawdown(net),
            }
        )
    return pd.DataFrame(rows)


def build_quintile_table(quintiles: pd.DataFrame) -> pd.DataFrame:
    """Average next-session outcome by score quintile (empirical frequencies, not forecasts)."""
    if quintiles.empty:
        return pd.DataFrame()
    grouped = quintiles.groupby("quintile")
    table = pd.DataFrame(
        {
            "mean_o2c_bps": grouped["o2c"].mean() * 1e4,
            "mean_c2c_bps": grouped["c2c"].mean() * 1e4,
            "positive_share_o2c": grouped["pos_o2c"].sum() / grouped["valid_o2c"].sum(),
            "observations": grouped["valid_o2c"].sum(),
        }
    )
    table.index.name = "score_quintile (5 = highest)"
    return table


def assess_edge(
    summary_stats: dict[str, Any], folds: pd.DataFrame, n_days: int, config: EvalConfig
) -> dict[str, Any]:
    """Apply the pre-registered rule. Passing it is necessary, not sufficient, for an edge."""
    low = summary_stats["net_excess_vs_universe_ci95_bps"][0]
    positive_share = (
        float((folds["net_excess_vs_universe_bps"] > 0).mean()) if not folds.empty else float("nan")
    )
    checks = {
        "enough_days": n_days >= config.min_eval_days,
        "ci_lower_bound_positive": bool(pd.notna(low) and low > 0),
        "enough_positive_folds": bool(
            pd.notna(positive_share) and positive_share >= config.min_positive_fold_share
        ),
        "net_return_positive": summary_stats["mean_net_return_bps"] > 0,
    }
    supported = all(checks.values())
    rule = (
        f">= {config.min_eval_days} evaluated days; 95% block-bootstrap lower bound of mean daily "
        "net excess return vs the equal-weight eligible universe > 0; at least "
        f"{config.min_positive_fold_share:.0%} of folds with positive net excess; mean net return > 0"
    )
    verdict = (
        "Out-of-sample results meet the pre-registered rule. This is necessary but NOT sufficient "
        "evidence of a live edge (see limitations: survivorship, idealised fills, single regime)."
        if supported
        else "No evidence of a predictive edge under the pre-registered rule. Do not rely on the "
        "ranking score."
    )
    return {
        "edge_supported": supported,
        "checks": checks,
        "positive_fold_share": positive_share,
        "rule": rule,
        "verdict": verdict,
    }


def run_walk_forward(
    frames: Mapping[str, pd.DataFrame],
    instruments: Mapping[str, Instrument],
    benchmarks: Mapping[str, pd.DataFrame],
    config: EvalConfig | None = None,
) -> WalkForwardResult:
    """Evaluate the scanner's score walk-forward on supplied price history.

    ``frames`` is keyed by ticker, ``instruments`` maps ticker -> Instrument and
    ``benchmarks`` maps exchange -> index OHLCV. Raises ValueError when too little
    history yields no evaluable dates, instead of reporting empty statistics as results.
    """
    cfg = config or EvalConfig()
    panel, index_outcomes, dropped = build_evaluation_panel(
        frames, instruments, benchmarks, cfg.scanner
    )
    daily, quintile_rows, skipped, eligible_counts = run_daily_selection(panel, index_outcomes, cfg)
    if daily.empty:
        raise ValueError("no evaluable dates: history too short or too few eligible symbols")

    summary, stats = summarise(daily, cfg)
    folds = build_folds(daily, cfg)
    quintiles = build_quintile_table(quintile_rows)
    assessment = assess_edge(stats, folds, len(daily), cfg)
    assessment.update({k: v for k, v in stats.items() if k not in assessment})

    dates = panel.index.get_level_values("date")
    score_valid = int(daily["score_o2c_valid"].sum())
    coverage = {
        "symbols_requested": len(instruments),
        "symbols_used": int(panel.index.get_level_values("ticker").nunique()),
        "symbols_dropped": {k: v for k, v in dropped.items()},
        "history_start": dates.min().date().isoformat(),
        "history_end": dates.max().date().isoformat(),
        "dates_evaluated": len(daily),
        "dates_skipped": skipped,
        "mean_eligible_per_date": float(np.mean(eligible_counts)) if eligible_counts else 0.0,
        "pick_outcomes_valid_share": score_valid / (len(daily) * cfg.top_k),
        "benchmark_available": bool(daily["index_o2c"].notna().any()),
    }
    return WalkForwardResult(
        summary=summary,
        folds=folds,
        quintiles=quintiles,
        daily=daily,
        coverage=coverage,
        assessment=assessment,
        round_trip_cost_bps=round_trip_cost_fraction(cfg.cost_model) * 1e4,
    )


def evaluate_from_provider(
    config: EvalConfig | None = None,
    *,
    universe: Iterable[Instrument | tuple[str, str]] | None = None,
    period: str = "5y",
    fetcher: FrameFetcher | None = None,
) -> WalkForwardResult:
    """Download history through the shared provider and run the walk-forward evaluation.

    Raises EvaluationDataError when the provider fails or returns nothing usable; stale or
    partial data is never silently substituted.
    """
    cfg = config or EvalConfig()
    instruments, _ = build_universe(universe, cfg.scanner)
    mapping: dict[str, Instrument] = {}
    for inst in instruments:
        ticker = ticker_for(inst)
        if ticker is not None and ticker not in mapping:
            mapping[ticker] = inst
    if not mapping:
        raise EvaluationDataError("universe is empty after validation")
    bench = benchmark_tickers(sorted({i.exchange for i in mapping.values()}))
    request = list(dict.fromkeys([*mapping, *bench.values()]))
    fetch = fetcher or default_frame_fetcher(period)
    try:
        frames, diagnostics = fetch(request)
    except Exception as exc:  # provider boundary: surface as a typed error, never hide
        raise EvaluationDataError(
            f"market-data provider failed: {type(exc).__name__}: {exc}"
        ) from exc
    benchmarks = {ex: frames[t] for ex, t in bench.items() if t in frames}
    if not any(t in frames for t in mapping):
        raise EvaluationDataError(f"provider returned no usable stock history: {dict(diagnostics)}")
    return run_walk_forward(frames, mapping, benchmarks, cfg)
