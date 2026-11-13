import json
from concurrent.futures import ThreadPoolExecutor
from time import sleep

import pytest

from scanner import dynamic_universe


def test_download_bse_equity_list_returns_numeric_scrip_codes(monkeypatch):
    payload = [
        {
            "SCRIP_CD": "500325",
            "scrip_id": "RELIANCE",
            "Status": "Active",
            "Segment": "Equity",
        },
        {
            "SCRIP_CD": "532540",
            "scrip_id": "TCS",
            "Status": "Active",
            "Segment": "Equity",
        },
        {
            "SCRIP_CD": "500001",
            "scrip_id": "INACTIVE",
            "Status": "Suspended",
            "Segment": "Equity",
        },
    ]

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(
        dynamic_universe,
        "urlopen",
        lambda *args, **kwargs: FakeResponse(),
    )

    assert dynamic_universe._download_bse_equity_list() == ["500325", "532540"]

    assert dynamic_universe.yahoo_symbol_for_bse_code("500325") == "RELIANCE"
    assert dynamic_universe.yahoo_symbol_for_bse_code("532540") == "TCS"
    assert dynamic_universe.yahoo_symbol_for_bse_code("500001") is None
    assert dynamic_universe.yahoo_symbol_for_bse_code("999999") is None


def test_curated_bse_fallback_maps_to_paired_company_symbols(monkeypatch):
    monkeypatch.setattr(dynamic_universe, "_bse_yahoo_symbol_map", {})

    assert dynamic_universe.yahoo_symbol_for_bse_code("500325") == "RELIANCE"
    assert dynamic_universe.yahoo_symbol_for_bse_code("532540") == "TCS"
    assert dynamic_universe.yahoo_symbol_for_bse_code("500001") is None
    assert dynamic_universe.yahoo_symbol_for_bse_code("999999") is None


def test_dynamic_bse_group_a_codes_uses_official_group_filter(monkeypatch):
    payload = [
        {"SCRIP_CD": "500325", "Status": "Active", "Segment": "Equity"},
        {"SCRIP_CD": "532540", "Status": "Active", "Segment": "Equity"},
        {"SCRIP_CD": "500001", "Status": "Suspended", "Segment": "Equity"},
        {"SCRIP_CD": "12345", "Status": "Active", "Segment": "Equity"},
    ]
    requested_urls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(payload).encode("utf-8")

    def fake_urlopen(request, timeout):
        requested_urls.append(request.full_url)
        assert timeout == 15
        return FakeResponse()

    monkeypatch.setattr(dynamic_universe, "urlopen", fake_urlopen)
    monkeypatch.setattr(dynamic_universe, "_cached_bse_group_a", None)

    assert dynamic_universe.dynamic_bse_group_a_codes() == {"500325", "532540"}
    assert "Group=A" in requested_urls[0]
    assert "segment=Equity" in requested_urls[0]
    assert "status=Active" in requested_urls[0]


def test_dynamic_bse_group_a_codes_returns_none_when_source_unavailable(monkeypatch):
    monkeypatch.setattr(dynamic_universe, "_cached_bse_group_a", None)

    def fail_urlopen(*args, **kwargs):
        raise OSError("BSE unavailable")

    monkeypatch.setattr(dynamic_universe, "urlopen", fail_urlopen)

    assert dynamic_universe.dynamic_bse_group_a_codes() is None


def test_dynamic_nse_fallback_is_cached_until_universe_ttl_expires(monkeypatch):
    now = [100.0]
    calls = []

    def fail_download():
        calls.append("NSE")
        raise OSError("NSE unavailable")

    monkeypatch.setattr(dynamic_universe, "time", type("Clock", (), {"time": lambda: now[0]}))
    monkeypatch.setattr(dynamic_universe, "_cached_nse_symbols", None)
    monkeypatch.setattr(dynamic_universe, "_download_nse_equity_list", fail_download)

    assert dynamic_universe.dynamic_nse_symbols() == dynamic_universe.NSE_CANDIDATES
    assert dynamic_universe.dynamic_nse_symbols() == dynamic_universe.NSE_CANDIDATES
    assert calls == ["NSE"]
    status = dynamic_universe.universe_source_status()["NSE"]
    assert status["source"] == "cached curated fallback"
    assert status["official_source_status"] == "source unavailable"
    assert status["reason"] == "OSError: NSE unavailable"

    now[0] += dynamic_universe.CACHE_TTL_SECONDS
    assert dynamic_universe.dynamic_nse_symbols() == dynamic_universe.NSE_CANDIDATES
    assert calls == ["NSE", "NSE"]


def test_dynamic_bse_fallback_is_cached_until_universe_ttl_expires(monkeypatch):
    now = [100.0]
    calls = []

    def fail_download():
        calls.append("BSE")
        raise OSError("BSE unavailable")

    monkeypatch.setattr(dynamic_universe, "time", type("Clock", (), {"time": lambda: now[0]}))
    monkeypatch.setattr(dynamic_universe, "_cached_bse_symbols", None)
    monkeypatch.setattr(dynamic_universe, "_download_bse_equity_list", fail_download)

    assert dynamic_universe.dynamic_bse_symbols() == dynamic_universe.BSE_CANDIDATES
    assert dynamic_universe.dynamic_bse_symbols() == dynamic_universe.BSE_CANDIDATES
    assert calls == ["BSE"]
    status = dynamic_universe.universe_source_status()["BSE"]
    assert status["source"] == "cached curated fallback"
    assert status["official_source_status"] == "source unavailable"
    assert status["reason"] == "OSError: BSE unavailable"

    now[0] += dynamic_universe.CACHE_TTL_SECONDS
    assert dynamic_universe.dynamic_bse_symbols() == dynamic_universe.BSE_CANDIDATES
    assert calls == ["BSE", "BSE"]


@pytest.mark.parametrize(
    ("exchange", "loader_name", "cache_name", "symbols"),
    [
        ("NSE", "_download_nse_equity_list", "_cached_nse_symbols", ["LIVE_NSE"]),
        ("BSE", "_download_bse_equity_list", "_cached_bse_symbols", ["500325"]),
    ],
)
def test_dynamic_universe_reports_official_and_cached_source(
    monkeypatch, exchange, loader_name, cache_name, symbols
):
    now = [100.0]
    calls = []
    monkeypatch.setattr(dynamic_universe, "time", type("Clock", (), {"time": lambda: now[0]}))
    monkeypatch.setattr(dynamic_universe, cache_name, None)
    monkeypatch.setitem(
        dynamic_universe._universe_source_status,
        exchange,
        {"source": "not loaded", "reason": "", "official_source_status": "not loaded"},
    )
    monkeypatch.setattr(dynamic_universe, loader_name, lambda: calls.append(exchange) or symbols)

    fetch = (
        dynamic_universe.dynamic_nse_symbols
        if exchange == "NSE"
        else dynamic_universe.dynamic_bse_symbols
    )
    assert fetch() == symbols
    assert dynamic_universe.universe_source_status()[exchange]["source"] == (
        "official live exchange source"
    )
    now[0] += 30
    assert fetch() == symbols
    status = dynamic_universe.universe_source_status()[exchange]
    assert status["source"] == "cached official exchange source"
    assert status["source_symbols"] == len(symbols)
    assert status["cache_age_seconds"] == 30
    assert calls == [exchange]

    now[0] += dynamic_universe.CACHE_TTL_SECONDS
    assert fetch() == symbols
    assert dynamic_universe.universe_source_status()[exchange]["source"] == (
        "official live exchange source"
    )
    assert calls == [exchange, exchange]


@pytest.mark.parametrize(
    ("exchange", "cache_name", "loader_name", "fallback"),
    [
        ("NSE", "_cached_nse_symbols", "_download_nse_equity_list", "NSE_CANDIDATES"),
        ("BSE", "_cached_bse_symbols", "_download_bse_equity_list", "BSE_CANDIDATES"),
    ],
)
def test_empty_official_response_uses_labeled_curated_fallback(
    monkeypatch, exchange, cache_name, loader_name, fallback
):
    monkeypatch.setattr(dynamic_universe, cache_name, None)
    monkeypatch.setattr(dynamic_universe, loader_name, lambda: [])
    monkeypatch.setitem(
        dynamic_universe._universe_source_status,
        exchange,
        {"source": "not loaded", "reason": "", "official_source_status": "not loaded"},
    )

    fetch = (
        dynamic_universe.dynamic_nse_symbols
        if exchange == "NSE"
        else dynamic_universe.dynamic_bse_symbols
    )
    assert fetch() == getattr(dynamic_universe, fallback)
    status = dynamic_universe.universe_source_status()[exchange]
    assert status["source"] == "curated fallback"
    assert status["official_source_status"] == "source unavailable"
    assert status["source_symbols"] == 0
    assert status["reason"] == "live source returned an empty symbol list"


def test_merge_reports_official_count_curated_additions_and_final_count(monkeypatch):
    live_symbols = ["RELIANCE", "LIVE_ONLY"]
    monkeypatch.setattr(dynamic_universe, "_cached_nse_symbols", None)
    monkeypatch.setattr(dynamic_universe, "_download_nse_equity_list", lambda: live_symbols)
    monkeypatch.setitem(
        dynamic_universe._universe_source_status,
        "NSE",
        {"source": "not loaded", "reason": "", "official_source_status": "not loaded"},
    )

    merged = dynamic_universe.merge_nse_universe(["CUSTOM_SYMBOL"])
    status = dynamic_universe.universe_source_status()["NSE"]
    expected_additions = len(set(dynamic_universe.NSE_CANDIDATES) - set(live_symbols))
    assert status["source_symbols"] == len(live_symbols)
    assert status["curated_additions"] == expected_additions
    assert status["merged_symbols"] == len(merged)
    assert "CUSTOM_SYMBOL" in merged


@pytest.mark.parametrize(
    ("exchange", "cache_name", "loader_name", "fetch_name", "symbols"),
    [
        (
            "NSE",
            "_cached_nse_symbols",
            "_download_nse_equity_list",
            "dynamic_nse_symbols",
            ["LIVE_NSE"],
        ),
        (
            "BSE",
            "_cached_bse_symbols",
            "_download_bse_equity_list",
            "dynamic_bse_symbols",
            ["500325"],
        ),
    ],
)
def test_concurrent_universe_refresh_is_coalesced(
    monkeypatch, exchange, cache_name, loader_name, fetch_name, symbols
):
    calls = []

    def fake_download():
        calls.append(exchange)
        sleep(0.05)
        return symbols

    monkeypatch.setattr(dynamic_universe, cache_name, None)
    monkeypatch.setattr(dynamic_universe, loader_name, fake_download)
    fetch = getattr(dynamic_universe, fetch_name)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: fetch(), range(8)))

    assert results == [symbols] * 8
    assert calls == [exchange]



def test_concurrent_bse_group_a_refresh_is_coalesced(monkeypatch):
    payload = [{"SCRIP_CD": "500325", "Status": "Active", "Segment": "Equity"}]
    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(payload).encode("utf-8")

    def fake_urlopen(*args, **kwargs):
        calls.append("BSE_GROUP_A")
        sleep(0.05)
        return FakeResponse()

    monkeypatch.setattr(dynamic_universe, "_cached_bse_group_a", None)
    monkeypatch.setattr(dynamic_universe, "urlopen", fake_urlopen)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: dynamic_universe.dynamic_bse_group_a_codes(), range(8)))

    assert results == [{"500325"}] * 8
    assert calls == ["BSE_GROUP_A"]


def test_concurrent_bse_group_a_failure_is_cached(monkeypatch):
    calls = []

    def fail_urlopen(*args, **kwargs):
        calls.append("BSE_GROUP_A")
        sleep(0.05)
        raise OSError("BSE unavailable")

    monkeypatch.setattr(dynamic_universe, "_cached_bse_group_a", None)
    monkeypatch.setattr(dynamic_universe, "urlopen", fail_urlopen)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: dynamic_universe.dynamic_bse_group_a_codes(), range(8)))

    assert results == [None] * 8
    assert calls == ["BSE_GROUP_A"]
