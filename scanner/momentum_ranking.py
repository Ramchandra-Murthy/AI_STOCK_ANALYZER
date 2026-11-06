"""Rank NSE/BSE symbols by intraday momentum strength.

This layer sits on top of :mod:`scanner.momentum_engine`. It is pure computation: no
network, no Streamlit, no global state. It only *orders* results the engine already
produced; it never scores, estimates or fills in anything itself.

Only results with a real score (``OK`` or ``PARTIAL``) are ranked. Symbols that are stale,
have too little data, are invalid, or were never returned by the provider are excluded and
reported by :func:`summarize_momentum` and :func:`unranked_table`, so a gap in coverage is
visible rather than hidden.

The ranking value is the engine's descriptive *momentum strength*. It is not a probability,
a forecast, or a buy/sell signal.
"""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from scanner.momentum_engine import WINDOWS, MomentumResult

EXCHANGE_SUFFIXES: Mapping[str, str] = {".NS": "NSE", ".BO": "BSE"}
EXCHANGE_CHOICES = ("NSE + BSE", "NSE", "BSE")
DEFAULT_TOP_N = 10
# Lower sorts first. A fully confirmed move outranks an equally scored partly confirmed one.
CONFIRMATION_ORDER: Mapping[str, int] = {"FULL": 0, "PARTIAL": 1, "NONE": 2}
# Scores equal to this many decimals are treated as ties and broken deterministically.
SCORE_TIE_DECIMALS = 6

RANKING_COLUMNS: tuple[str, ...] = (
    "Rank",
    "Exchange rank",
    "Symbol",
    "Exchange",
    "Momentum strength",
    "Direction",
    "Confirmation",
    "Volume state",
    "Volume ratio",
    *(f"{window}m %" for window in WINDOWS),
    "Score coverage",
    "Status",
    "Data age (s)",
)
UNRANKED_COLUMNS: tuple[str, ...] = ("Symbol", "Exchange", "Status", "Reasons")


def exchange_of(ticker: str) -> str | None:
    """Return ``"NSE"`` / ``"BSE"`` from a Yahoo ticker suffix, or ``None`` if unknown."""
    text = str(ticker).strip().upper()
    for suffix, exchange in EXCHANGE_SUFFIXES.items():
        if text.endswith(suffix):
            return exchange
    return None


def bare_symbol(ticker: str) -> str:
    """Strip a known exchange suffix: ``RELIANCE.NS`` -> ``RELIANCE``."""
    text = str(ticker).strip().upper()
    for suffix in EXCHANGE_SUFFIXES:
        if text.endswith(suffix):
            return text[: -len(suffix)]
    return text


def _sort_key(item: tuple[str, MomentumResult]) -> tuple[float, int, float, str]:
    ticker, result = item
    score = round(float(result.score or 0.0), SCORE_TIE_DECIMALS)
    confirmation = CONFIRMATION_ORDER.get(result.timeframe_confirmation, len(CONFIRMATION_ORDER))
    ratio = result.volume_ratio
    # Missing volume never beats a measured surge; it just sorts after it.
    volume = -float(ratio) if ratio is not None else float("inf")
    return (-score, confirmation, volume, ticker)


def _scored(results: Mapping[str, MomentumResult]) -> list[tuple[str, MomentumResult]]:
    return sorted(
        ((ticker, result) for ticker, result in results.items() if result.is_scored),
        key=_sort_key,
    )


def _row(ticker: str, result: MomentumResult, rank: int, exchange_rank: int) -> dict[str, object]:
    row: dict[str, object] = {
        "Rank": rank,
        "Exchange rank": exchange_rank,
        "Symbol": bare_symbol(ticker),
        "Exchange": exchange_of(ticker),
        "Momentum strength": None if result.score is None else round(float(result.score), 1),
        "Direction": result.direction,
        "Confirmation": result.timeframe_confirmation,
        "Volume state": result.volume_state,
        "Volume ratio": result.volume_ratio,
    }
    for window in WINDOWS:
        value = result.returns.get(window)
        row[f"{window}m %"] = None if value is None else round(value * 100.0, 4)
    row["Score coverage"] = round(float(result.score_coverage), 3)
    row["Status"] = result.status
    row["Data age (s)"] = result.data_age_seconds
    return row


def rank_momentum(
    results: Mapping[str, MomentumResult],
    *,
    top_n: int | None = DEFAULT_TOP_N,
) -> pd.DataFrame:
    """Rank scored results across NSE and BSE, best first.

    ``results`` is keyed by Yahoo ticker (``RELIANCE.NS``), so the same company listed on
    both exchanges stays two separate rows. Order is momentum strength (descending), then
    timeframe confirmation (FULL before PARTIAL before NONE), then volume ratio (higher
    first, missing last), then ticker, so the ranking is fully deterministic.

    ``Exchange rank`` is the position within the symbol's own exchange among *all* scored
    symbols. ``top_n=None`` returns every scored symbol.
    """
    ordered = _scored(results)
    seen: dict[str | None, int] = {}
    rows: list[dict[str, object]] = []
    for position, (ticker, result) in enumerate(ordered, start=1):
        exchange = exchange_of(ticker)
        seen[exchange] = seen.get(exchange, 0) + 1
        rows.append(_row(ticker, result, position, seen[exchange]))
    frame = pd.DataFrame(rows, columns=list(RANKING_COLUMNS))
    if top_n is not None:
        frame = frame.head(max(0, int(top_n)))
    return frame.reset_index(drop=True)


def view_ranking(
    ranking: pd.DataFrame,
    *,
    exchange: str = "NSE + BSE",
    top_n: int | None = DEFAULT_TOP_N,
) -> pd.DataFrame:
    """Filter a full ranking to one exchange and renumber ``Rank`` for what is shown.

    This only hides rows; ``Exchange rank`` and every score are left untouched.
    """
    if ranking is None or ranking.empty:
        return pd.DataFrame(columns=list(RANKING_COLUMNS))
    view = ranking.copy()
    if exchange in {"NSE", "BSE"}:
        view = view.loc[view["Exchange"].eq(exchange)]
    if top_n is not None:
        view = view.head(max(0, int(top_n)))
    view = view.reset_index(drop=True)
    view["Rank"] = range(1, len(view) + 1)
    return view


def summarize_momentum(
    results: Mapping[str, MomentumResult],
    *,
    requested: int | None = None,
) -> dict[str, int]:
    """Count how many symbols were scored and why the others were not.

    ``requested`` is the number of symbols asked of the provider; any not present in
    ``results`` are reported as ``missing_from_provider``.
    """
    counts: dict[str, int] = {}
    for result in results.values():
        counts[result.status] = counts.get(result.status, 0) + 1
    scored = sum(1 for result in results.values() if result.is_scored)
    total = len(results) if requested is None else max(int(requested), len(results))
    summary = {
        "requested": total,
        "scored": scored,
        "unscored": len(results) - scored,
        "missing_from_provider": total - len(results),
    }
    summary.update({f"status_{status}": count for status, count in sorted(counts.items())})
    return summary


def unranked_table(results: Mapping[str, MomentumResult]) -> pd.DataFrame:
    """List the symbols that could not be ranked, with the engine's reasons."""
    rows = [
        {
            "Symbol": bare_symbol(ticker),
            "Exchange": exchange_of(ticker),
            "Status": result.status,
            "Reasons": ", ".join(result.reasons),
        }
        for ticker, result in sorted(results.items())
        if not result.is_scored
    ]
    return pd.DataFrame(rows, columns=list(UNRANKED_COLUMNS))
