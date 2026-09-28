from algorithmic_trading.algorithmic_scanner import _ticker


def test_ticker_uses_exchange_suffix() -> None:
    assert _ticker("RELIANCE", "NSE") == "RELIANCE.NS"
    assert _ticker("500325", "BSE") == "500325.BO"


def test_ticker_does_not_duplicate_suffix() -> None:
    assert _ticker("RELIANCE.NS", "NSE") == "RELIANCE.NS"
