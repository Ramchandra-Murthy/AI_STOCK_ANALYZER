"""Options analytics foundation for the Streamlit scanner.

The module deliberately keeps the data-provider boundary separate from the UI.
Yahoo Finance is used as the first provider because it is already part of the
application dependency set. Availability and timestamps are surfaced rather
than inferred when a provider does not expose an Indian index option chain.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yfinance as yf

OPTIONS_UNDERLYINGS = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
}

CHAIN_COLUMNS = [
    "strike",
    "CE LTP",
    "CE volume",
    "CE OI",
    "CE OI change",
    "CE IV",
    "PE LTP",
    "PE volume",
    "PE OI",
    "PE OI change",
    "PE IV",
    "PCR OI",
]


@dataclass(frozen=True)
class OptionChainResult:
    """Provider result with explicit availability diagnostics."""

    underlying: str
    provider_symbol: str
    expiry: str | None
    spot: float | None
    chain: pd.DataFrame
    expiries: tuple[str, ...]
    status: str
    message: str


def available_expiries(underlying: str) -> tuple[str, ...]:
    """Return provider-reported expiries for an underlying."""
    symbol = OPTIONS_UNDERLYINGS[underlying]
    ticker = yf.Ticker(symbol)
    try:
        return tuple(str(expiry) for expiry in ticker.options)
    except Exception:
        return ()


def fetch_option_chain(
    underlying: str,
    expiry: str | None = None,
) -> OptionChainResult:
    """Fetch and normalize an option chain without inventing missing data."""
    if underlying not in OPTIONS_UNDERLYINGS:
        raise ValueError(f"Unsupported underlying: {underlying}")

    symbol = OPTIONS_UNDERLYINGS[underlying]
    ticker = yf.Ticker(symbol)
    try:
        expiries = tuple(str(value) for value in ticker.options)
    except Exception as exc:
        return OptionChainResult(
            underlying,
            symbol,
            expiry,
            None,
            pd.DataFrame(columns=CHAIN_COLUMNS),
            (),
            "UNAVAILABLE",
            f"Option expiries could not be loaded from Yahoo Finance: {exc}",
        )

    if not expiries:
        return OptionChainResult(
            underlying,
            symbol,
            expiry,
            _spot_price(ticker),
            pd.DataFrame(columns=CHAIN_COLUMNS),
            (),
            "UNAVAILABLE",
            "Yahoo Finance did not expose an option chain for this underlying.",
        )

    selected_expiry = expiry if expiry in expiries else expiries[0]
    try:
        raw = ticker.option_chain(selected_expiry)
        chain = _normalize_chain(raw.calls, raw.puts)
    except Exception as exc:
        return OptionChainResult(
            underlying,
            symbol,
            selected_expiry,
            _spot_price(ticker),
            pd.DataFrame(columns=CHAIN_COLUMNS),
            expiries,
            "UNAVAILABLE",
            f"Option chain could not be loaded: {exc}",
        )

    if chain.empty:
        status = "UNAVAILABLE"
        message = "The provider returned an empty option chain."
    else:
        status = "AVAILABLE"
        message = "Option chain loaded from Yahoo Finance."

    return OptionChainResult(
        underlying,
        symbol,
        selected_expiry,
        _spot_price(ticker),
        chain,
        expiries,
        status,
        message,
    )


def summarize_option_chain(chain: pd.DataFrame) -> pd.DataFrame:
    """Calculate descriptive OI and volume statistics from a normalized chain."""
    if chain.empty:
        return pd.DataFrame(columns=["Metric", "Value"])

    call_oi = pd.to_numeric(chain["CE OI"], errors="coerce").fillna(0)
    put_oi = pd.to_numeric(chain["PE OI"], errors="coerce").fillna(0)
    call_volume = pd.to_numeric(chain["CE volume"], errors="coerce").fillna(0)
    put_volume = pd.to_numeric(chain["PE volume"], errors="coerce").fillna(0)
    total_call_oi = float(call_oi.sum())
    total_put_oi = float(put_oi.sum())

    pcr = total_put_oi / total_call_oi if total_call_oi else None
    max_call = _max_oi_strike(chain, "CE OI")
    max_put = _max_oi_strike(chain, "PE OI")

    rows = [
        ("Call OI", total_call_oi),
        ("Put OI", total_put_oi),
        ("PCR (OI)", pcr),
        ("Call volume", float(call_volume.sum())),
        ("Put volume", float(put_volume.sum())),
        ("Highest Call OI strike", max_call),
        ("Highest Put OI strike", max_put),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def _normalize_chain(calls: pd.DataFrame, puts: pd.DataFrame) -> pd.DataFrame:
    call = calls.copy()
    put = puts.copy()
    for frame in (call, put):
        for column in ["strike", "lastPrice", "volume", "openInterest", "impliedVolatility"]:
            if column not in frame.columns:
                frame[column] = pd.NA

    if "changeinOpenInterest" not in call.columns:
        call["changeinOpenInterest"] = pd.NA
    if "changeinOpenInterest" not in put.columns:
        put["changeinOpenInterest"] = pd.NA

    call = call[
        [
            "strike",
            "lastPrice",
            "volume",
            "openInterest",
            "changeinOpenInterest",
            "impliedVolatility",
        ]
    ].rename(
        columns={
            "lastPrice": "CE LTP",
            "volume": "CE volume",
            "openInterest": "CE OI",
            "changeinOpenInterest": "CE OI change",
            "impliedVolatility": "CE IV",
        }
    )
    put = put[
        ["strike", "lastPrice", "volume", "openInterest", "changeinOpenInterest", "impliedVolatility"]
    ].rename(
        columns={
            "lastPrice": "PE LTP",
            "volume": "PE volume",
            "openInterest": "PE OI",
            "changeinOpenInterest": "PE OI change",
            "impliedVolatility": "PE IV",
        }
    )

    chain = call.merge(put, on="strike", how="outer").sort_values("strike").reset_index(drop=True)
    call_oi = pd.to_numeric(chain["CE OI"], errors="coerce")
    put_oi = pd.to_numeric(chain["PE OI"], errors="coerce")
    chain["PCR OI"] = put_oi.div(call_oi.where(call_oi.ne(0)))
    return chain[CHAIN_COLUMNS]


def _max_oi_strike(chain: pd.DataFrame, column: str) -> float | None:
    values = pd.to_numeric(chain[column], errors="coerce")
    if values.dropna().empty:
        return None
    return float(chain.loc[values.idxmax(), "strike"])


def _spot_price(ticker: yf.Ticker) -> float | None:
    try:
        history = ticker.history(period="1d", interval="1m")
        if history.empty:
            return None
        return float(history["Close"].dropna().iloc[-1])
    except Exception:
        return None
