import json

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

    now[0] += dynamic_universe.CACHE_TTL_SECONDS
    assert dynamic_universe.dynamic_bse_symbols() == dynamic_universe.BSE_CANDIDATES
    assert calls == ["BSE", "BSE"]
