"""Options analytics providers for the Streamlit scanner.

NSE is the primary provider for Indian index option chains. Yahoo Finance remains
an explicit fallback because it is already part of the application dependency set.
Provider availability and timestamps are surfaced rather than inferred.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.request import Request, urlopen

import pandas as pd
import yfinance as yf

OPTIONS_UNDERLYINGS = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
}

NSE_OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices"
NSE_HEADERS = {
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/option-chain",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0 Safari/537.36"
    ),
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
    """Return provider-reported expiries, preferring NSE."""
    if underlying not in OPTIONS_UNDERLYINGS:
        raise ValueError(f"Unsupported underlying: {underlying}")

    try:
        payload = _fetch_nse_option_chain(underlying)
        expiries = _nse_expiries(payload)
        if expiries:
            return expiries
    except Exception:
        pass

    symbol = OPTIONS_UNDERLYINGS[underlying]
    try:
        return tuple(str(expiry) for expiry in yf.Ticker(symbol).options)
    except Exception:
        return ()


def fetch_option_chain(
    underlying: str,
    expiry: str | None = None,
) -> OptionChainResult:
    """Fetch and normalize an Indian index option chain."""
    if underlying not in OPTIONS_UNDERLYINGS:
        raise ValueError(f"Unsupported underlying: {underlying}")

    try:
        payload = _fetch_nse_option_chain(underlying)
        expiries = _nse_expiries(payload)
        if expiries:
            selected_expiry = expiry if expiry in expiries else expiries[0]
            chain = _normalize_nse_chain(payload, selected_expiry)
            spot = _nse_spot(payload)
            if not chain.empty:
                return OptionChainResult(
                    underlying,
                    f"NSE:{underlying}",
                    selected_expiry,
                    spot,
                    chain,
                    expiries,
                    "AVAILABLE",
                    "Option chain loaded from NSE.",
                )
    except Exception as exc:
        nse_error = str(exc)
    else:
        nse_error = "NSE returned no usable option-chain expiries."

    yahoo_result = _fetch_yahoo_option_chain(underlying, expiry)
    if yahoo_result.status == "AVAILABLE":
        return yahoo_result

    message = (
        f"NSE option-chain data was unavailable ({nse_error}); "
        f"Yahoo Finance fallback was also unavailable ({yahoo_result.message})."
    )
    return OptionChainResult(
        underlying,
        yahoo_result.provider_symbol,
        yahoo_result.expiry,
        yahoo_result.spot,
        yahoo_result.chain,
        yahoo_result.expiries,
        "UNAVAILABLE",
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


def _fetch_nse_option_chain(underlying: str) -> dict:
    """Fetch the public NSE index option-chain JSON with browser-like headers."""
    request = Request(
        f"{NSE_OPTION_CHAIN_URL}?symbol={underlying}",
        headers=NSE_HEADERS,
        method="GET",
    )
    with urlopen(request, timeout=12) as response:
        if response.status != 200:
            raise RuntimeError(f"NSE returned HTTP {response.status}.")
        return json.loads(response.read().decode("utf-8"))


def _nse_expiries(payload: dict) -> tuple[str, ...]:
    records = payload.get("records", {})
    values = records.get("expiryDates", [])
    return tuple(str(value) for value in values if value)


def _nse_spot(payload: dict) -> float | None:
    value = payload.get("records", {}).get("underlyingValue")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _normalize_nse_chain(payload: dict, expiry: str) -> pd.DataFrame:
    rows = []
    for item in payload.get("records", {}).get("data", []):
        if str(item.get("expiryDate")) != expiry:
            continue
        call = item.get("CE") or {}
        put = item.get("PE") or {}
        rows.append(
            {
                "strike": item.get("strikePrice"),
                "CE LTP": call.get("lastPrice"),
                "CE volume": call.get("totalTradedVolume"),
                "CE OI": call.get("openInterest"),
                "CE OI change": call.get("changeinOpenInterest"),
                "CE IV": call.get("impliedVolatility"),
                "PE LTP": put.get("lastPrice"),
                "PE volume": put.get("totalTradedVolume"),
                "PE OI": put.get("openInterest"),
                "PE OI change": put.get("changeinOpenInterest"),
                "PE IV": put.get("impliedVolatility"),
            }
        )

    if not rows:
        return pd.DataFrame(columns=CHAIN_COLUMNS)

    return _finalize_chain(pd.DataFrame(rows))


def _fetch_yahoo_option_chain(
    underlying: str,
    expiry: str | None,
) -> OptionChainResult:
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
            f"Yahoo Finance expiries could not be loaded: {exc}",
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
            f"Yahoo Finance option chain could not be loaded: {exc}",
        )

    if chain.empty:
        return OptionChainResult(
            underlying,
            symbol,
            selected_expiry,
            _spot_price(ticker),
            chain,
            expiries,
            "UNAVAILABLE",
            "Yahoo Finance returned an empty option chain.",
        )

    return OptionChainResult(
        underlying,
        symbol,
        selected_expiry,
        _spot_price(ticker),
        chain,
        expiries,
        "AVAILABLE",
        "Option chain loaded from Yahoo Finance fallback.",
    )


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
            "lastPrice": "PE LTP",
            "volume": "PE volume",
            "openInterest": "PE OI",
            "changeinOpenInterest": "PE OI change",
            "impliedVolatility": "PE IV",
        }
    )

    chain = call.merge(put, on="strike", how="outer")
    return _finalize_chain(chain)


def _finalize_chain(chain: pd.DataFrame) -> pd.DataFrame:
    chain = chain.sort_values("strike").reset_index(drop=True)
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
