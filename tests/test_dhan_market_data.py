from services.dhan_market_data import (
    NIFTY_50_SECURITY_ID,
    NIFTY_INDEX_SEGMENT,
    DhanConfigurationError,
    DhanCredentials,
    DhanMarketData,
)


class FakeDhanClient:
    def ticker_data(self, securities):
        return {"status": "success", "data": securities}

    def ohlc_data(self, securities):
        return {"status": "success", "data": securities}

    def quote_data(self, securities):
        return {"status": "success", "data": securities}

    def expiry_list(self, security_id, segment):
        return {"status": "success", "data": [security_id, segment]}

    def option_chain(self, security_id, segment, expiry):
        return {"status": "success", "data": [security_id, segment, expiry]}


def test_dhan_credentials_load_without_exposing_values():
    credentials = DhanCredentials.from_env(
        {
            "DHAN_CLIENT_ID": "client-123",
            "DHAN_ACCESS_TOKEN": "secret-token",
        }
    )

    assert credentials.client_id == "client-123"
    assert credentials.access_token == "secret-token"


def test_dhan_credentials_reject_missing_values():
    try:
        DhanCredentials.from_env({"DHAN_CLIENT_ID": "client-123"})
    except DhanConfigurationError as exc:
        assert "DHAN_ACCESS_TOKEN" in str(exc)
    else:
        raise AssertionError("Expected missing Dhan access-token configuration to fail")


def test_dhan_market_data_uses_read_only_quote_methods():
    dhan = DhanMarketData(client=FakeDhanClient())

    assert dhan.ticker_data({"NSE_EQ": [1333]})["status"] == "success"
    assert dhan.ohlc_data({"NSE_EQ": [1333]})["status"] == "success"
    assert dhan.quote_data({"NSE_EQ": [1333]})["status"] == "success"


def test_nifty_helpers_use_dhan_index_contract():
    dhan = DhanMarketData(client=FakeDhanClient())

    assert dhan.nifty_ltp()["data"] == {NIFTY_INDEX_SEGMENT: [NIFTY_50_SECURITY_ID]}
    assert dhan.nifty_expiries()["data"] == [NIFTY_50_SECURITY_ID, NIFTY_INDEX_SEGMENT]
    assert dhan.nifty_option_chain("2026-10-13")["data"] == [
        NIFTY_50_SECURITY_ID,
        NIFTY_INDEX_SEGMENT,
        "2026-10-13",
    ]


class FailingOptionClient(FakeDhanClient):
    def expiry_list(self, security_id, segment):
        return {
            "status": "failure",
            "remarks": {
                "error_code": None,
                "error_type": None,
                "error_message": None,
            },
        }

    def option_chain(self, security_id, segment, expiry):
        return {
            "status": "failure",
            "remarks": {
                "error_code": None,
                "error_type": None,
                "error_message": None,
            },
        }


class FakeHttpResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        import json

        return json.dumps(self._payload).encode("utf-8")


def test_option_apis_retry_with_direct_dhan_rest(monkeypatch):
    import services.dhan_market_data as module

    calls = []

    def fake_urlopen(request, timeout):
        headers = {key.lower(): value for key, value in request.header_items()}
        calls.append((request.full_url, headers.get("client-id"), timeout))
        if request.full_url.endswith("/expirylist"):
            raise AssertionError("unexpected URL")
        return FakeHttpResponse(
            {"status": "success", "data": {"last_price": 25000, "oc": {}}}
        )

    def fake_option_urlopen(request, timeout):
        headers = {key.lower(): value for key, value in request.header_items()}
        calls.append((request.full_url, headers.get("client-id"), timeout))
        return FakeHttpResponse({"status": "success", "data": ["direct"]})

    monkeypatch.setattr(module, "urlopen", fake_option_urlopen)
    credentials = DhanCredentials("client-123", "secret-token")
    dhan = DhanMarketData(credentials=credentials, client=FailingOptionClient())

    response = dhan.option_chain(13, "IDX_I", "2026-10-08")

    assert response["status"] == "success"
    assert calls == [("https://api.dhan.co/v2/optionchain", "client-123", 15)]
