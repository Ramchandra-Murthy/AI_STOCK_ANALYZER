import pandas as pd

from services import market_service


def test_get_top_movers_returns_up_to_ten_gainers_and_losers(monkeypatch):
    frame = pd.DataFrame(
        {
            "Symbol": [f"STOCK{i}" for i in range(12)],
            "Change %": [float(value) for value in range(-6, 6)],
        }
    )
    monkeypatch.setattr(market_service, "_scan_watchlist", lambda _watchlist: frame)

    gainers, losers = market_service.get_top_movers()

    assert len(gainers) == 10
    assert len(losers) == 10
    assert gainers["Change %"].is_monotonic_decreasing
    assert losers["Change %"].is_monotonic_increasing
    assert (gainers["Change %"] > 0).all()
    assert (losers["Change %"] < 0).all()


def test_get_top_movers_returns_empty_frames_when_no_quotes(monkeypatch):
    empty = pd.DataFrame(columns=["Symbol", "Change %"])
    monkeypatch.setattr(market_service, "_scan_watchlist", lambda _watchlist: empty)

    gainers, losers = market_service.get_top_movers()

    assert gainers.empty
    assert losers.empty


def test_dashboard_component_uses_shared_lightweight_view(monkeypatch):
    import components.market_movers as dashboard_movers
    import modules.market_movers as page_movers

    calls = []
    monkeypatch.setattr(page_movers, "show", lambda: calls.append("rendered"))

    dashboard_movers.show_market_movers()

    assert calls == ["rendered"]
