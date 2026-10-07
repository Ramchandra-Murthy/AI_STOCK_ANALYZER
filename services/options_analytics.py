"""Options analytics providers for the Streamlit scanner.

Dhan is the primary provider for Indian index option chains. NSE and Yahoo Finance
remain fallbacks for environments where Dhan is not configured or unavailable.
Provider availability and timestamps are surfaced rather than inferred.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

import pandas as pd
import yfinance as yf

from services.dhan_market_data import DhanCredentials, DhanMarketData

OPTIONS_UNDERLYINGS = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
}

DHAN_OPTION_UNDERLYINGS = {
    "NIFTY": (13, "IDX_I"),
    "BANKNIFTY": (25, "IDX_I"),
    "FINNIFTY": (27, "IDX_I"),
}

NSE_HOME_URL = "https://www.nseindia.com/"
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
NSE_RETRY_DELAY_SECONDS = 1.0
_NSE_OPENER = build_opener(HTTPCookieProcessor(CookieJar()))

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
        dhan_expiries = _fetch_dhan_expiries(underlying)
        if dhan_expiries:
            return dhan_expiries
    except Exception:
        pass

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
        dhan_result = _fetch_dhan_option_chain(underlying, expiry)
        if dhan_result.status == "AVAILABLE":
            return dhan_result
        dhan_error = dhan_result.message
    except Exception as exc:
        dhan_error = str(exc)

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
                    "Option chain loaded from NSE fallback.",
                )
    except Exception as exc:
        nse_error = str(exc)
    else:
        nse_error = "NSE returned no usable option-chain expiries."

    yahoo_result = _fetch_yahoo_option_chain(underlying, expiry)
    if yahoo_result.status == "AVAILABLE":
        return yahoo_result

    message = (
        f"Dhan option-chain data was unavailable ({dhan_error}); "
        f"NSE fallback was unavailable ({nse_error}); "
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


def _dhan_expiry(value: str) -> str:
    """Convert the legacy NSE display expiry to Dhan's YYYY-MM-DD format."""
    try:
        return pd.Timestamp(value).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return str(value)


def _fetch_dhan_expiries(underlying: str) -> tuple[str, ...]:
    """Return Dhan-reported expiries when Dhan credentials are configured."""
    if underlying not in DHAN_OPTION_UNDERLYINGS:
        return ()
    credentials = DhanCredentials.from_env()
    client = DhanMarketData(credentials=credentials)
    security_id, segment = DHAN_OPTION_UNDERLYINGS[underlying]
    response = client.expiry_list(security_id, segment)
    if not isinstance(response, dict) or response.get("status") != "success":
        remarks = response.get("remarks", response) if isinstance(response, dict) else response
        raise RuntimeError(f"Dhan expiry list failed: {remarks}")
    values = response.get("data", [])
    if not isinstance(values, list):
        raise RuntimeError("Dhan expiry list returned an invalid data payload.")
    return tuple(str(value) for value in values if value)


def _normalize_dhan_chain(
    payload: dict,
    underlying: str,
    expiry: str,
    expiries: tuple[str, ...],
) -> OptionChainResult:
    data = payload.get("data", {})
    if not isinstance(data, dict):
        raise RuntimeError("Dhan option-chain response has no data object.")
    raw_chain = data.get("oc", {})
    if not isinstance(raw_chain, dict):
        raise RuntimeError("Dhan option-chain response has no strike map.")

    rows = []
    for strike_text, strike_data in raw_chain.items():
        if not isinstance(strike_data, dict):
            continue
        call = strike_data.get("ce") or {}
        put = strike_data.get("pe") or {}
        if not isinstance(call, dict):
            call = {}
        if not isinstance(put, dict):
            put = {}

        def oi_change(option: dict) -> float | None:
            oi = option.get("oi")
            previous_oi = option.get("previous_oi")
            try:
                if oi is None or previous_oi is None:
                    return None
                return float(oi) - float(previous_oi)
            except (TypeError, ValueError):
                return None

        try:
            strike_price = float(strike_text)
        except (TypeError, ValueError):
            continue

        rows.append(
            {
                "strike": strike_price,
                "CE LTP": call.get("last_price"),
                "CE volume": call.get("volume"),
                "CE OI": call.get("oi"),
                "CE OI change": oi_change(call),
                "CE IV": call.get("implied_volatility"),
                "PE LTP": put.get("last_price"),
                "PE volume": put.get("volume"),
                "PE OI": put.get("oi"),
                "PE OI change": oi_change(put),
                "PE IV": put.get("implied_volatility"),
            }
        )

    chain = _finalize_chain(pd.DataFrame(rows)) if rows else pd.DataFrame(columns=CHAIN_COLUMNS)
    spot = data.get("last_price")
    try:
        spot_value = float(spot) if spot is not None else None
    except (TypeError, ValueError):
        spot_value = None

    if chain.empty:
        raise RuntimeError("Dhan returned an empty option chain.")

    return OptionChainResult(
        underlying,
        f"Dhan:{underlying}",
        expiry,
        spot_value,
        chain,
        expiries,
        "AVAILABLE",
        "Option chain loaded from Dhan.",
    )


def _fetch_dhan_option_chain(
    underlying: str,
    expiry: str | None = None,
) -> OptionChainResult:
    """Fetch an index option chain from Dhan when credentials are configured."""
    if underlying not in DHAN_OPTION_UNDERLYINGS:
        raise ValueError(f"Unsupported underlying: {underlying}")

    credentials = DhanCredentials.from_env()
    client = DhanMarketData(credentials=credentials)
    security_id, segment = DHAN_OPTION_UNDERLYINGS[underlying]

    expiry_values = _fetch_dhan_expiries(underlying)
    if not expiry_values:
        raise RuntimeError("Dhan returned no active option expiries.")

    requested = _dhan_expiry(expiry) if expiry else None
    selected = requested if requested in expiry_values else expiry_values[0]
    response = client.option_chain(security_id, segment, selected)

    if not isinstance(response, dict) or response.get("status") != "success":
        remarks = response.get("remarks", response) if isinstance(response, dict) else response
        raise RuntimeError(f"Dhan option chain failed: {remarks}")

    return _normalize_dhan_chain(response, underlying, selected, expiry_values)


def _fetch_nse_option_chain(underlying: str) -> dict:
    """Fetch NSE option-chain JSON using a primed browser-like session."""
    _prime_nse_session()
    request = Request(
        f"{NSE_OPTION_CHAIN_URL}?symbol={underlying}",
        headers=NSE_HEADERS,
        method="GET",
    )
    try:
        with _NSE_OPENER.open(request, timeout=12) as response:
            if response.status != 200:
                raise RuntimeError(f"NSE returned HTTP {response.status}.")
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code not in (403, 429):
            raise
        time.sleep(NSE_RETRY_DELAY_SECONDS)
        _prime_nse_session()
        with _NSE_OPENER.open(request, timeout=12) as response:
            if response.status != 200:
                raise RuntimeError(f"NSE returned HTTP {response.status}.") from exc
            return json.loads(response.read().decode("utf-8"))


def _prime_nse_session() -> None:
    """Prime NSE cookies before requesting the protected option-chain endpoint."""
    request = Request(
        NSE_HOME_URL,
        headers={
            **NSE_HEADERS,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        method="GET",
    )
    try:
        with _NSE_OPENER.open(request, timeout=10):
            pass
    except Exception:
        # The API request below remains the source of truth; some environments
        # block the NSE homepage while allowing the API endpoint.
        pass


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
