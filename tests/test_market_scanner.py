import pandas as pd

from scanner.market_scanner import _extract_series


def test_extract_series_supports_ticker_first_columns() -> None:
    columns = pd.MultiIndex.from_product([["RELIANCE.NS"], ["Close", "Volume"]])
    frame = pd.DataFrame([[100.0, 1_000_000]], columns=columns)

    assert _extract_series(frame, "RELIANCE.NS", "Close").tolist() == [100.0]


def test_extract_series_supports_field_first_columns() -> None:
    columns = pd.MultiIndex.from_product([["Close", "Volume"], ["RELIANCE.NS"]])
    frame = pd.DataFrame([[100.0, 1_000_000]], columns=columns)

    assert _extract_series(frame, "RELIANCE.NS", "Volume").tolist() == [1_000_000]


def test_market_scan_uses_only_requested_exchange(monkeypatch) -> None:
    from scanner import market_scanner

    calls = []
    monkeypatch.setattr(market_scanner, "merge_nse_universe", lambda: ["RELIANCE"])
    monkeypatch.setattr(market_scanner, "merge_bse_universe", lambda: ["500325"])
    monkeypatch.setattr(
        market_scanner,
        "_batch_change_screen",
        lambda candidates: calls.append(candidates) or [],
    )

    result = market_scanner.market_scan("BSE")

    assert result.empty
    assert calls == [{"BSE": ["500325"]}]


def test_market_scan_includes_both_exchanges_by_default(monkeypatch) -> None:
    from scanner import market_scanner

    calls = []
    monkeypatch.setattr(market_scanner, "merge_nse_universe", lambda: ["RELIANCE"])
    monkeypatch.setattr(market_scanner, "merge_bse_universe", lambda: ["500325"])
    monkeypatch.setattr(
        market_scanner,
        "_batch_change_screen",
        lambda candidates: calls.append(candidates) or [],
    )

    result = market_scanner.market_scan()

    assert result.empty
    assert calls == [{"NSE": ["RELIANCE"], "BSE": ["500325"]}]
