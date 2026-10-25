from scanner import market_scanner


def test_market_scan_exposes_stage_timings_when_screen_has_no_movers(monkeypatch) -> None:
    monkeypatch.setattr(market_scanner, "merge_nse_universe", lambda: ["RELIANCE"])
    monkeypatch.setattr(market_scanner, "_batch_change_screen", lambda candidates, coverage=None: [])

    result = market_scanner.market_scan("NSE")

    assert result.empty
    timings = result.attrs["scanner_timings"]
    assert timings["universe_build_seconds"] >= 0
    assert timings["screen_seconds"] >= 0
    assert timings["total_seconds"] >= timings["screen_seconds"]
    assert "analysis_download_seconds" not in timings
