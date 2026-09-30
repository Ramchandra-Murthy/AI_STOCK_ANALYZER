from components.top10_live import TOP10_REFRESH_SECONDS, show_live_top10_scanner


def test_top10_live_scanner_refreshes_every_minute() -> None:
    assert TOP10_REFRESH_SECONDS == 60
    assert callable(show_live_top10_scanner)
