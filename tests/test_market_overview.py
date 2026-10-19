from components.market_overview import _market_status_banner


def _status(name):
    return name, {"status": name, "detail": "test"}


def test_market_banner_warns_when_any_index_is_stale():
    level, message = _market_status_banner(
        [
            _status("INTRADAY DATA · TODAY"),
            _status("STALE INTRADAY DATA"),
            _status("INTRADAY DATA · TODAY"),
        ]
    )

    assert level == "warning"
    assert "STALE INTRADAY DATA" in message


def test_market_banner_is_success_only_when_all_indices_are_current_intraday():
    level, message = _market_status_banner(
        [
            _status("INTRADAY DATA · TODAY"),
            _status("INTRADAY DATA · TODAY"),
        ]
    )

    assert level == "success"
    assert "not exchange-tick live" in message


def test_market_banner_warns_when_an_index_falls_back_to_daily_data_during_session():
    level, message = _market_status_banner(
        [
            _status("INTRADAY DATA · TODAY"),
            _status("DAILY DATA ONLY · INTRADAY UNAVAILABLE"),
        ]
    )

    assert level == "warning"
    assert "DAILY DATA ONLY · INTRADAY UNAVAILABLE" in message


def test_market_banner_reports_closed_session_without_claiming_live_data():
    level, message = _market_status_banner(
        [
            _status("MARKET CLOSED · TODAY'S DATA"),
            _status("MARKET CLOSED · TODAY'S DATA"),
        ]
    )

    assert level == "info"
    assert "MARKET CLOSED · TODAY'S DATA" in message
