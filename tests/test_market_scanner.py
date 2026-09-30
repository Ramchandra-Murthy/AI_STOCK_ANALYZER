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
