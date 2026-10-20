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
