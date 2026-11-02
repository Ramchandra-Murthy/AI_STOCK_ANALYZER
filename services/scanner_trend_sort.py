"""Shared bullish-to-bearish ordering for scanner result tables."""


_TREND_RANKS = {
    "STRONG BULLISH": 0,
    "BULLISH": 1,
    "LONG": 1,
    "BUY": 1,
    "POSITIVE": 1,
    "UPTREND": 1,
    "SIDEWAYS": 2,
    "NEUTRAL": 2,
    "RANGE / MIXED": 2,
    "MIXED": 2,
    "UNKNOWN": 3,
    "INSUFFICIENT DATA": 3,
    "BEARISH": 4,
    "SHORT": 4,
    "SELL": 4,
    "NEGATIVE": 4,
    "DOWNTREND": 4,
    "STRONG BEARISH": 5,
}


def _trend_rank(value: object) -> int:
    """Map explicit trend/signal labels to a stable bullish-first rank."""
    label = str(value).strip().upper().replace("_", " ").replace("-", " ")
    if not label or label in {"NAN", "NONE", "NAT"}:
        return 3
    if "INSUFFICIENT" in label or "UNKNOWN" in label or "UNAVAILABLE" in label:
        return 3
    if "STRONG" in label and ("BEAR" in label or "SHORT" in label):
        return 5
    if "STRONG" in label and ("BULL" in label or "LONG" in label):
        return 0
    if any(token in label for token in ("BEAR", "SHORT", "SELL", "DOWN", "NEGATIVE")):
        return 4
    if any(token in label for token in ("BULL", "LONG", "BUY", "UPTREND", "POSITIVE")):
        return 1
    if any(token in label for token in ("SIDEWAYS", "NEUTRAL", "MIXED", "RANGE")):
        return 2
    return 3


def sort_bullish_to_bearish(
    frame: object,
    *,
    trend_columns: tuple[str, ...] = ("Trend", "trend", "regime", "signal", "Recommendation"),
    strength_columns: tuple[str, ...] = (
        "AI Score", "score", "confidence_pct", "confidence", "trend_pct",
        "Change %", "Change 30m %", "Change 15m %", "Change 5m %",
    ),
) -> object:
    """Sort scanner rows bullish-to-bearish without changing signal values.

    Uses the first available explicit trend/signal column, then the first available
    strength column descending. Unknown labels are always placed after known regimes.
    """
    # Keep this utility independent of pandas imports so Ruff does not treat a
    # single third-party import as an incomplete import block.
    if frame is None or not hasattr(frame, "empty"):
        return frame
    if frame.empty:
        return frame.copy()

    result = frame.copy()
    trend_column = next((column for column in trend_columns if column in result.columns), None)
    if trend_column is None:
        # Do not invent trend labels when a scanner exposes only numeric returns.
        return result

    rank_name = "__trend_order_rank__"
    while rank_name in result.columns:
        rank_name = f"_{rank_name}"
    result[rank_name] = result[trend_column].map(_trend_rank)

    strength_column = next((column for column in strength_columns if column in result.columns), None)
    temporary_columns = [rank_name]
    sort_columns = [rank_name]
    ascending = [True]
    if strength_column is not None:
        strength_name = "__trend_order_strength__"
        while strength_name in result.columns:
            strength_name = f"_{strength_name}"
        result[strength_name] = pd.to_numeric(result[strength_column], errors="coerce")
        temporary_columns.append(strength_name)
        sort_columns.append(strength_name)
        ascending.append(False)

    result = result.sort_values(sort_columns, ascending=ascending, na_position="last", kind="stable")
    return result.drop(columns=temporary_columns).reset_index(drop=True)
