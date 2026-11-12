from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
from time import sleep

import pandas as pd
import pytest

from services import resilient_market_data as market_data


@pytest.fixture(autouse=True)
def _clear_market_data_cache():
    market_data.clear_market_data_cache()
    market_data.clear_market_data_runtime_stats()
    market_data.clear_market_metadata_cache()
    market_data.clear_company_name_cache()
    market_data._reset_provider_circuit_breaker()
    yield
    market_data.clear_market_data_cache()
    market_data.clear_market_metadata_cache()
    market_data.clear_company_name_cache()
    market_data._reset_provider_circuit_breaker()


def _frame() -> pd.DataFrame:
    index = pd.date_range("2026-10-05", periods=3, freq="min")
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [101.0, 102.0, 103.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [100.5, 101.5, 102.5],
            "Volume": [1000, 1100, 1200],
        },
        index=index,
    )


def test_download_symbol_frames_recovers_missing_symbols(monkeypatch) -> None:
    def fake_batch(tickers, **_kwargs):
        return (
            pd.concat(
                {"AAA.NS": _frame()},
                axis=1,
            )
            if "AAA.NS" in tickers
            else pd.DataFrame()
        )

    monkeypatch.setattr(market_data, "_download_batch", fake_batch)
    monkeypatch.setattr(market_data, "_download_single", lambda ticker, **_: _frame())

    frames, missing = market_data.download_symbol_frames(
        ["AAA.NS", "BBB.NS"],
        period="5d",
        interval="1m",
        batch_size=10,
    )

    assert set(frames) == {"AAA.NS", "BBB.NS"}
    assert missing == []


def test_download_market_frames_reports_unresolved_symbols(monkeypatch) -> None:
    monkeypatch.setattr(
        market_data,
        "_download_batch",
        lambda *_args, **_kwargs: pd.DataFrame(),
    )
    monkeypatch.setattr(
        market_data,
        "_download_single",
        lambda *_args, **_kwargs: pd.DataFrame(),
    )

    frames, diagnostics = market_data.download_market_frames(
        ["AAA.NS", "BBB.NS"],
        period="5d",
        interval="1m",
    )

    assert frames == {}
    assert diagnostics["requested"] == 2
    assert diagnostics["usable"] == 0
    assert diagnostics["coverage_pct"] == 0.0
    assert diagnostics["complete"] is False
    assert diagnostics["missing"] == ["AAA.NS", "BBB.NS"]


def test_download_symbol_frames_splits_universe_into_bounded_batches(monkeypatch) -> None:
    batch_calls: list[list[str]] = []

    def fake_batch(tickers, **_kwargs):
        batch_calls.append(list(tickers))
        return pd.concat({ticker: _frame() for ticker in tickers}, axis=1)

    monkeypatch.setattr(market_data, "_download_batch", fake_batch)
    monkeypatch.setattr(
        market_data,
        "_download_single",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("single-symbol recovery should not run when batch data is complete")
        ),
    )

    tickers = [f"STOCK{i}.NS" for i in range(23)]
    diagnostics: list[str] = []
    frames, missing = market_data.download_symbol_frames(
        tickers,
        period="5y",
        interval="1d",
        batch_size=10,
        diagnostics=diagnostics,
    )

    assert sorted(len(batch) for batch in batch_calls) == [3, 10, 10]
    assert any(
        "download summary:" in item
        and "batches=3" in item
        and "single_recovery_attempts=0" in item
        and "total_seconds=" in item
        for item in diagnostics
    )
    assert sorted(ticker for batch in batch_calls for ticker in batch) == sorted(tickers)
    assert set(frames) == set(tickers)
    assert missing == []


def test_download_symbol_frames_can_report_missing_without_single_recovery(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        market_data,
        "_download_batch",
        lambda *_args, **_kwargs: pd.DataFrame(),
    )
    monkeypatch.setattr(
        market_data,
        "_download_single",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("single-symbol recovery must be disabled")
        ),
    )

    frames, missing = market_data.download_symbol_frames(
        ["AAA.NS", "BBB.NS"],
        period="5y",
        interval="1d",
        recover_missing=False,
    )

    assert frames == {}
    assert missing == ["AAA.NS", "BBB.NS"]


def test_download_market_frames_reports_safe_failure_diagnostics(monkeypatch) -> None:
    monkeypatch.setattr(
        market_data,
        "_download_batch",
        lambda *_args, diagnostics=None, **_kwargs: (
            diagnostics.append("batch request returned no rows")
            if diagnostics is not None
            else None
        )
        or pd.DataFrame(),
    )

    frames, diagnostics = market_data.download_market_frames(
        ["AAA.NS"],
        period="1d",
        interval="1m",
        recover_missing=False,
    )

    assert frames == {}
    assert diagnostics["requested"] == 1
    assert diagnostics["usable"] == 0
    assert diagnostics["missing"] == ["AAA.NS"]
    assert diagnostics["complete"] is False
    assert diagnostics["failure_diagnostics"] == ["batch request returned no rows"]


class _FakeTicker:
    """Stand-in for ``yf.Ticker`` that records how many history requests are made."""

    requests: list[str] = []
    responses: dict[str, pd.DataFrame] = {}

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker

    def history(self, **_kwargs) -> pd.DataFrame:
        type(self).requests.append(self.ticker)
        return type(self).responses.get(self.ticker, pd.DataFrame())


def _install_fake_ticker(monkeypatch, responses: dict[str, pd.DataFrame]) -> list[float]:
    _FakeTicker.requests = []
    _FakeTicker.responses = responses
    sleeps: list[float] = []
    monkeypatch.setattr(market_data.yf, "Ticker", _FakeTicker)
    monkeypatch.setattr(market_data, "sleep", sleeps.append)
    return sleeps


def test_download_single_makes_exactly_one_request_without_retries(monkeypatch) -> None:
    sleeps = _install_fake_ticker(monkeypatch, {})

    frame = market_data._download_single(
        "AAA.NS", period="1d", interval="1m", auto_adjust=False, timeout=4, retries=0
    )

    assert frame.empty
    assert _FakeTicker.requests == ["AAA.NS"]
    assert sleeps == []


def test_download_single_keeps_default_retries_with_backoff(monkeypatch) -> None:
    sleeps = _install_fake_ticker(monkeypatch, {})

    market_data._download_single("AAA.NS", period="1d", interval="1m", auto_adjust=False, timeout=4)

    assert len(_FakeTicker.requests) == market_data.DEFAULT_RETRIES + 1
    assert len(sleeps) == market_data.DEFAULT_RETRIES


def test_download_symbols_individually_recovers_available_symbols(monkeypatch) -> None:
    _install_fake_ticker(monkeypatch, {"BBB.NS": _frame()})

    frames, missing = market_data.download_symbols_individually(
        ["AAA.NS", "BBB.NS", "CCC.NS"], period="1d", interval="1m", retries=0
    )

    assert set(frames) == {"BBB.NS"}
    assert missing == ["AAA.NS", "CCC.NS"]
    assert _FakeTicker.requests == ["AAA.NS", "BBB.NS", "CCC.NS"]


def test_download_symbols_individually_caps_the_number_of_requests(monkeypatch) -> None:
    _install_fake_ticker(monkeypatch, {})
    symbols = [f"S{i}.NS" for i in range(10)]

    frames, missing = market_data.download_symbols_individually(
        symbols, period="1d", interval="1m", retries=0, max_symbols=3
    )

    assert frames == {}
    assert _FakeTicker.requests == symbols[:3]  # hard cap on provider requests
    assert missing == symbols  # unattempted symbols stay unresolved, never invented


def test_download_symbols_individually_never_fabricates_frames(monkeypatch) -> None:
    _install_fake_ticker(monkeypatch, {})

    frames, missing = market_data.download_symbols_individually(
        ["AAA.NS", "AAA.NS", " bbb.ns "], period="1d", interval="1m", retries=0
    )

    assert frames == {}
    assert missing == ["AAA.NS", "BBB.NS"]  # de-duplicated and normalised


def test_batch_then_single_recovery_with_mocked_provider(monkeypatch) -> None:
    """A batch that resolves only some symbols is completed by direct requests."""

    def partial_batch(tickers, **_kwargs):
        return pd.concat({"AAA.NS": _frame()}, axis=1) if "AAA.NS" in tickers else pd.DataFrame()

    monkeypatch.setattr(market_data, "_download_batch", partial_batch)
    _install_fake_ticker(monkeypatch, {"BBB.NS": _frame()})

    frames, missing = market_data.download_symbol_frames(
        ["AAA.NS", "BBB.NS", "CCC.NS"],
        period="1d",
        interval="1m",
        recover_missing=True,
    )

    assert set(frames) == {"AAA.NS", "BBB.NS"}
    assert missing == ["CCC.NS"]


def test_download_symbol_frames_reuses_fresh_cached_frames(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_batch(tickers, **_kwargs):
        calls.append(list(tickers))
        return pd.concat({ticker: _frame() for ticker in tickers}, axis=1)

    monkeypatch.setattr(market_data, "_download_batch", fake_batch)
    first, first_missing = market_data.download_symbol_frames(
        ["AAA.NS", "BBB.NS"], period="1d", interval="1m", recover_missing=False
    )
    second, second_missing = market_data.download_symbol_frames(
        ["AAA.NS", "BBB.NS"], period="1d", interval="1m", recover_missing=False
    )

    assert set(first) == set(second) == {"AAA.NS", "BBB.NS"}
    assert first_missing == second_missing == []
    assert calls == [["AAA.NS", "BBB.NS"]]
    assert market_data.market_data_cache_stats()["entries"] == 2


def test_market_data_cache_returns_independent_frame_copies(monkeypatch) -> None:
    monkeypatch.setattr(
        market_data,
        "_download_batch",
        lambda tickers, **_kwargs: pd.concat({ticker: _frame() for ticker in tickers}, axis=1),
    )
    first, _ = market_data.download_symbol_frames(
        ["AAA.NS"], period="1d", interval="5m", recover_missing=False
    )
    first["AAA.NS"].iloc[0, first["AAA.NS"].columns.get_loc("Close")] = -1
    second, _ = market_data.download_symbol_frames(
        ["AAA.NS"], period="1d", interval="5m", recover_missing=False
    )

    assert second["AAA.NS"]["Close"].iloc[0] == 100.5


def test_market_data_cache_ttl_expiry_triggers_provider_refresh(monkeypatch) -> None:
    clock = [100.0]
    calls: list[int] = []

    monkeypatch.setattr(market_data, "monotonic", lambda: clock[0])

    def fake_batch(tickers, **_kwargs):
        calls.append(1)
        return pd.concat({ticker: _frame() for ticker in tickers}, axis=1)

    monkeypatch.setattr(market_data, "_download_batch", fake_batch)
    market_data.download_symbol_frames(
        ["AAA.NS"],
        period="1d",
        interval="1m",
        recover_missing=False,
        cache_ttl_seconds=5,
    )
    clock[0] += 6
    market_data.download_symbol_frames(
        ["AAA.NS"],
        period="1d",
        interval="1m",
        recover_missing=False,
        cache_ttl_seconds=5,
    )

    assert len(calls) == 2
    assert market_data.market_data_cache_stats()["entries"] == 1


def test_zero_cache_ttl_forces_a_fresh_provider_request(monkeypatch) -> None:
    calls: list[int] = []

    def fake_batch(tickers, **_kwargs):
        calls.append(1)
        return pd.concat({ticker: _frame() for ticker in tickers}, axis=1)

    monkeypatch.setattr(market_data, "_download_batch", fake_batch)
    for _ in range(2):
        market_data.download_symbol_frames(
            ["AAA.NS"],
            period="1d",
            interval="1m",
            recover_missing=False,
            cache_ttl_seconds=0,
        )

    assert len(calls) == 2


def test_market_cap_metadata_is_cached_and_uses_provider(monkeypatch) -> None:
    market_data.clear_market_metadata_cache()
    calls = []

    class FakeTicker:
        def __init__(self, ticker, **kwargs):
            calls.append((ticker, kwargs))

        @property
        def fast_info(self):
            return {"market_cap": 123456.0}

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)

    first = market_data.get_market_cap("AAA.NS")
    second = market_data.get_market_cap("AAA.NS")

    assert first == second == 123456.0
    assert calls == [("AAA.NS", {"timeout": market_data.DEFAULT_TIMEOUT})]


def test_market_cap_metadata_negative_cache_expires(monkeypatch) -> None:
    market_data.clear_market_metadata_cache()
    clock = [100.0]
    calls: list[str] = []
    monkeypatch.setattr(market_data, "monotonic", lambda: clock[0])

    class FakeTicker:
        def __init__(self, ticker: str, **_kwargs) -> None:
            calls.append(ticker)

        @property
        def fast_info(self) -> dict[str, None]:
            return {"market_cap": None}

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)

    assert market_data.get_market_cap("AAA.NS", negative_cache_ttl_seconds=10) is None
    assert market_data.get_market_cap("AAA.NS", negative_cache_ttl_seconds=10) is None
    assert calls == ["AAA.NS"]

    clock[0] += 11
    assert market_data.get_market_cap("AAA.NS", negative_cache_ttl_seconds=10) is None
    assert calls == ["AAA.NS", "AAA.NS"]


def test_market_cap_negative_cache_can_be_disabled(monkeypatch) -> None:
    calls: list[str] = []

    class FakeTicker:
        def __init__(self, ticker: str, **_kwargs) -> None:
            calls.append(ticker)

        @property
        def fast_info(self) -> dict[str, None]:
            return {"market_cap": None}

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)

    for _ in range(2):
        assert market_data.get_market_cap("AAA.NS", negative_cache_ttl_seconds=0) is None

    assert calls == ["AAA.NS", "AAA.NS"]


def test_company_name_metadata_is_cached_and_provider_request_is_shared(monkeypatch) -> None:
    calls: list[str] = []

    class FakeTicker:
        def __init__(self, ticker: str, **_kwargs) -> None:
            self.ticker = ticker

        def get_info(self) -> dict[str, str]:
            calls.append(self.ticker)
            return {"longName": "Example Industries"}

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)

    assert market_data.get_company_name("example.ns") == "Example Industries"
    assert market_data.get_company_name("EXAMPLE.NS") == "Example Industries"
    assert calls == ["EXAMPLE.NS"]


def test_company_name_negative_cache_expires(monkeypatch) -> None:
    clock = [100.0]
    calls: list[str] = []
    monkeypatch.setattr(market_data, "monotonic", lambda: clock[0])

    class FakeTicker:
        def __init__(self, ticker: str, **_kwargs) -> None:
            self.ticker = ticker

        def get_info(self) -> dict[str, str]:
            calls.append(self.ticker)
            return {}

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)

    assert market_data.get_company_name("UNKNOWN.NS", negative_cache_ttl_seconds=10) == "UNKNOWN.NS"
    assert market_data.get_company_name("UNKNOWN.NS", negative_cache_ttl_seconds=10) == "UNKNOWN.NS"
    assert calls == ["UNKNOWN.NS"]

    clock[0] += 11
    assert market_data.get_company_name("UNKNOWN.NS", negative_cache_ttl_seconds=10) == "UNKNOWN.NS"
    assert calls == ["UNKNOWN.NS", "UNKNOWN.NS"]


def test_company_name_negative_cache_can_be_disabled(monkeypatch) -> None:
    calls: list[str] = []

    class FakeTicker:
        def __init__(self, ticker: str, **_kwargs) -> None:
            self.ticker = ticker

        def get_info(self) -> dict[str, str]:
            calls.append(self.ticker)
            return {}

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)

    for _ in range(2):
        assert (
            market_data.get_company_name("UNKNOWN.NS", negative_cache_ttl_seconds=0) == "UNKNOWN.NS"
        )

    assert calls == ["UNKNOWN.NS", "UNKNOWN.NS"]


def test_runtime_telemetry_tracks_cache_hits_and_misses(monkeypatch) -> None:
    monkeypatch.setattr(
        market_data,
        "_download_batch",
        lambda tickers, **_kwargs: pd.concat({ticker: _frame() for ticker in tickers}, axis=1),
    )
    market_data.download_symbol_frames(
        ["AAA.NS"], period="1d", interval="1m", recover_missing=False
    )
    market_data.download_symbol_frames(
        ["AAA.NS"], period="1d", interval="1m", recover_missing=False
    )

    stats = market_data.market_data_runtime_stats()
    assert stats["scan_calls"] == 2
    assert stats["cache_misses"] == 1
    assert stats["cache_hits"] == 1
    assert stats["total_scan_seconds"] >= 0
    assert stats["cache_entries"] == 1


def test_concurrent_identical_batch_downloads_are_coalesced(monkeypatch) -> None:
    calls: list[list[str]] = []
    calls_lock = Lock()
    provider_started = Event()
    release_provider = Event()

    def fake_batch(tickers, **_kwargs):
        with calls_lock:
            calls.append(list(tickers))
        provider_started.set()
        assert release_provider.wait(timeout=3)
        return pd.concat({ticker: _frame() for ticker in tickers}, axis=1)

    monkeypatch.setattr(market_data, "_download_batch", fake_batch)

    def fetch():
        return market_data.download_symbol_frames(
            ["AAA.NS", "BBB.NS"],
            period="1d",
            interval="1m",
            recover_missing=False,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(fetch)
        assert provider_started.wait(timeout=2)
        second_future = executor.submit(fetch)
        # Give the second caller time to join the already-running batch Future.
        sleep(0.1)
        release_provider.set()
        first, first_missing = first_future.result(timeout=3)
        second, second_missing = second_future.result(timeout=3)

    assert calls == [["AAA.NS", "BBB.NS"]]
    assert first_missing == second_missing == []
    assert set(first) == set(second) == {"AAA.NS", "BBB.NS"}

    first["AAA.NS"].iloc[0, first["AAA.NS"].columns.get_loc("Close")] = -1
    assert second["AAA.NS"]["Close"].iloc[0] == 100.5


def test_download_symbol_frames_caps_single_symbol_recovery(monkeypatch) -> None:
    batch_calls: list[list[str]] = []
    single_calls: list[str] = []

    def empty_batch(tickers, **_kwargs):
        batch_calls.append(list(tickers))
        return pd.DataFrame()

    def empty_single(ticker, **_kwargs):
        single_calls.append(ticker)
        return pd.DataFrame()

    monkeypatch.setattr(market_data, "_download_batch", empty_batch)
    monkeypatch.setattr(market_data, "_download_single", empty_single)
    symbols = [f"S{i}.NS" for i in range(100)]
    diagnostics: list[str] = []

    frames, missing = market_data.download_symbol_frames(
        symbols,
        period="1d",
        interval="1m",
        batch_size=100,
        recover_missing=True,
        recovery_max_symbols=20,
        retries=0,
        diagnostics=diagnostics,
    )

    assert frames == {}
    assert missing == symbols
    assert len(batch_calls) == 1
    assert single_calls == symbols[:20]
    assert any("single_recovery_attempts=20" in item for item in diagnostics)


def test_download_symbol_frames_can_disable_recovery_with_zero_budget(monkeypatch) -> None:
    single_calls: list[str] = []
    monkeypatch.setattr(market_data, "_download_batch", lambda *_args, **_kwargs: pd.DataFrame())
    monkeypatch.setattr(
        market_data,
        "_download_single",
        lambda ticker, **_kwargs: single_calls.append(ticker) or pd.DataFrame(),
    )

    _frames, missing = market_data.download_symbol_frames(
        ["AAA.NS", "BBB.NS"],
        period="1d",
        interval="1m",
        recover_missing=True,
        recovery_max_symbols=0,
        retries=0,
    )

    assert missing == ["AAA.NS", "BBB.NS"]
    assert single_calls == []


def test_recovery_stops_at_time_budget(monkeypatch) -> None:
    clock = [0.0]
    calls: list[str] = []

    def fake_batch(_tickers, **_kwargs):
        return pd.DataFrame()

    def fake_single(ticker, **_kwargs):
        calls.append(ticker)
        clock[0] += 3.0
        return pd.DataFrame()

    monkeypatch.setattr(market_data, "_download_batch", fake_batch)
    monkeypatch.setattr(market_data, "perf_counter", lambda: clock[0])
    monkeypatch.setattr(market_data, "_download_single", fake_single)

    symbols = [f"S{i}.NS" for i in range(10)]
    frames, missing = market_data.download_symbol_frames(
        symbols,
        period="1d",
        interval="1m",
        batch_size=10,
        recover_missing=True,
        max_recovery_symbols=10,
        max_recovery_seconds=5.0,
        retries=0,
    )

    assert frames == {}
    assert calls == symbols[:2]
    assert missing == symbols


def test_cache_hit_does_not_extend_absolute_ttl(monkeypatch) -> None:
    clock = [100.0]
    provider_versions = [0]
    calls: list[int] = []
    monkeypatch.setattr(market_data, "monotonic", lambda: clock[0])

    def fake_batch(tickers, **_kwargs):
        version = provider_versions[0]
        calls.append(version)
        frame = _frame().copy()
        frame["Close"] = frame["Close"] + version * 100
        return pd.concat({ticker: frame for ticker in tickers}, axis=1)

    monkeypatch.setattr(market_data, "_download_batch", fake_batch)

    first, _ = market_data.download_symbol_frames(
        ["AAA.NS"], period="1d", interval="1m", recover_missing=False, cache_ttl_seconds=5
    )
    provider_versions[0] = 1
    clock[0] = 104.0
    within_ttl, _ = market_data.download_symbol_frames(
        ["AAA.NS"], period="1d", interval="1m", recover_missing=False, cache_ttl_seconds=5
    )
    clock[0] = 106.0
    expired, _ = market_data.download_symbol_frames(
        ["AAA.NS"], period="1d", interval="1m", recover_missing=False, cache_ttl_seconds=5
    )

    assert first["AAA.NS"]["Close"].iloc[-1] == 102.5
    assert within_ttl["AAA.NS"]["Close"].iloc[-1] == 102.5
    assert expired["AAA.NS"]["Close"].iloc[-1] == 202.5
    assert calls == [0, 1]


def test_provider_circuit_opens_after_three_failures_and_suppresses_requests(monkeypatch) -> None:
    clock = [100.0]
    monkeypatch.setattr(market_data, "monotonic", lambda: clock[0])

    for _ in range(market_data.PROVIDER_CIRCUIT_FAILURE_THRESHOLD):
        market_data._provider_circuit_record_failure()

    assert market_data.provider_circuit_breaker_stats()["state"] == "open"
    diagnostics: list[str] = []
    assert market_data._provider_circuit_allows_request(diagnostics) is False
    assert any("request suppressed" in item for item in diagnostics)


def test_provider_circuit_allows_only_one_half_open_probe_and_recovers(monkeypatch) -> None:
    clock = [100.0]
    monkeypatch.setattr(market_data, "monotonic", lambda: clock[0])

    for _ in range(market_data.PROVIDER_CIRCUIT_FAILURE_THRESHOLD):
        market_data._provider_circuit_record_failure()

    clock[0] += market_data.PROVIDER_CIRCUIT_COOLDOWN_SECONDS
    assert market_data._provider_circuit_allows_request() is True
    assert market_data.provider_circuit_breaker_stats()["state"] == "half_open"
    assert market_data._provider_circuit_allows_request() is False

    market_data._provider_circuit_record_success()
    stats = market_data.provider_circuit_breaker_stats()
    assert stats["state"] == "closed"
    assert stats["trips"] == 0
    assert stats["probe_in_flight"] is False


def test_provider_circuit_reopens_with_exponential_cooldown_after_probe_failure(
    monkeypatch,
) -> None:
    clock = [100.0]
    monkeypatch.setattr(market_data, "monotonic", lambda: clock[0])

    for _ in range(market_data.PROVIDER_CIRCUIT_FAILURE_THRESHOLD):
        market_data._provider_circuit_record_failure()
    clock[0] += market_data.PROVIDER_CIRCUIT_COOLDOWN_SECONDS

    assert market_data._provider_circuit_allows_request() is True
    market_data._provider_circuit_record_failure()

    stats = market_data.provider_circuit_breaker_stats()
    assert stats["state"] == "open"
    assert stats["cooldown_seconds"] == 60.0
    assert stats["trips"] == 2


def test_provider_circuit_does_not_leave_probe_reserved_after_request_setup_error(
    monkeypatch,
) -> None:
    clock = [100.0]
    monkeypatch.setattr(market_data, "monotonic", lambda: clock[0])
    for _ in range(market_data.PROVIDER_CIRCUIT_FAILURE_THRESHOLD):
        market_data._provider_circuit_record_failure()
    clock[0] += market_data.PROVIDER_CIRCUIT_COOLDOWN_SECONDS

    assert market_data._provider_circuit_allows_request() is True
    market_data._provider_circuit_cancel_probe()

    stats = market_data.provider_circuit_breaker_stats()
    assert stats["state"] == "half_open"
    assert stats["probe_in_flight"] is False
    assert market_data._provider_circuit_allows_request() is True


def test_provider_circuit_exponential_cooldown_is_capped(monkeypatch) -> None:
    clock = [100.0]
    monkeypatch.setattr(market_data, "monotonic", lambda: clock[0])

    market_data._provider_circuit_record_failure()
    market_data._provider_circuit_record_failure()
    market_data._provider_circuit_record_failure()

    expected_cooldown = market_data.PROVIDER_CIRCUIT_COOLDOWN_SECONDS
    for _ in range(6):
        stats = market_data.provider_circuit_breaker_stats()
        assert stats["state"] == "open"
        assert stats["cooldown_seconds"] == expected_cooldown

        clock[0] += expected_cooldown
        assert market_data._provider_circuit_allows_request() is True
        market_data._provider_circuit_record_failure()

        expected_cooldown = min(
            expected_cooldown * 2,
            market_data.PROVIDER_CIRCUIT_MAX_COOLDOWN_SECONDS,
        )
        stats = market_data.provider_circuit_breaker_stats()
        assert stats["state"] == "open"
        assert stats["cooldown_seconds"] == expected_cooldown


def test_negative_metadata_cache_is_bounded_and_evicts_oldest(monkeypatch) -> None:
    market_data.clear_market_metadata_cache()
    market_data.clear_company_name_cache()
    limit = market_data._NEGATIVE_METADATA_CACHE_MAX_ENTRIES
    clock = [500.0]
    calls: list[str] = []
    monkeypatch.setattr(market_data, "monotonic", lambda: clock[0])

    class FakeTicker:
        def __init__(self, ticker: str, **_kwargs) -> None:
            self.ticker = ticker

        @property
        def fast_info(self) -> dict[str, None]:
            calls.append(self.ticker)
            return {"market_cap": None}

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)
    for index in range(limit + 1):
        assert market_data.get_market_cap(f"S{index}.NS", negative_cache_ttl_seconds=60) is None

    assert len(market_data._NEGATIVE_METADATA_CACHE) == limit
    assert "S0.NS" not in market_data._NEGATIVE_METADATA_CACHE
    assert "S1.NS" in market_data._NEGATIVE_METADATA_CACHE
    assert len(calls) == limit + 1


def test_company_name_negative_cache_is_bounded_and_evicts_oldest(monkeypatch) -> None:
    market_data.clear_company_name_cache()
    limit = market_data._NEGATIVE_METADATA_CACHE_MAX_ENTRIES
    calls: list[str] = []

    class FakeTicker:
        def __init__(self, ticker: str, **_kwargs) -> None:
            self.ticker = ticker

        def get_info(self) -> dict[str, str]:
            calls.append(self.ticker)
            return {}

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)
    for index in range(limit + 1):
        assert market_data.get_company_name(f"S{index}.NS", negative_cache_ttl_seconds=60) == (
            f"S{index}.NS"
        )

    assert len(market_data._COMPANY_NAME_NEGATIVE_CACHE) == limit
    assert "S0.NS" not in market_data._COMPANY_NAME_NEGATIVE_CACHE
    assert "S1.NS" in market_data._COMPANY_NAME_NEGATIVE_CACHE
    assert len(calls) == limit + 1


def test_metadata_cache_invalidation_clears_positive_and_negative_entries(monkeypatch) -> None:
    class MissingTicker:
        def __init__(self, ticker: str, **_kwargs) -> None:
            self.ticker = ticker

        @property
        def fast_info(self) -> dict[str, None]:
            return {"market_cap": None}

        def get_info(self) -> dict[str, str]:
            return {}

    monkeypatch.setattr(market_data.yf, "Ticker", MissingTicker)
    assert market_data.get_market_cap("MISS.NS") is None
    assert market_data.get_company_name("MISS.NS") == "MISS.NS"
    assert "MISS.NS" in market_data._NEGATIVE_METADATA_CACHE
    assert "MISS.NS" in market_data._COMPANY_NAME_NEGATIVE_CACHE

    market_data.clear_market_metadata_cache()
    market_data.clear_company_name_cache()

    assert "MISS.NS" not in market_data._NEGATIVE_METADATA_CACHE
    assert "MISS.NS" not in market_data._COMPANY_NAME_NEGATIVE_CACHE


def test_metadata_provider_exceptions_are_not_negative_cached(monkeypatch) -> None:
    calls: list[str] = []

    class FailingTicker:
        def __init__(self, ticker: str, **_kwargs) -> None:
            self.ticker = ticker

        @property
        def fast_info(self):
            calls.append(self.ticker)
            raise TimeoutError("provider timeout")

        def get_info(self):
            calls.append(self.ticker)
            raise TimeoutError("provider timeout")

    monkeypatch.setattr(market_data.yf, "Ticker", FailingTicker)
    for _ in range(2):
        assert market_data.get_market_cap("TIMEOUT.NS") is None
        assert market_data.get_company_name("TIMEOUT.NS") == "TIMEOUT.NS"

    assert calls == ["TIMEOUT.NS"] * 4
    assert "TIMEOUT.NS" not in market_data._NEGATIVE_METADATA_CACHE
    assert "TIMEOUT.NS" not in market_data._COMPANY_NAME_NEGATIVE_CACHE

def test_negative_metadata_cache_is_thread_safe(monkeypatch) -> None:
    market_data.clear_market_metadata_cache()
    calls: list[str] = []
    calls_lock = Lock()

    class FakeTicker:
        def __init__(self, ticker: str, **_kwargs) -> None:
            self.ticker = ticker

        @property
        def fast_info(self) -> dict[str, None]:
            with calls_lock:
                calls.append(self.ticker)
            return {"market_cap": None}

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)

    def lookup():
        return market_data.get_market_cap("THREAD.NS", negative_cache_ttl_seconds=60)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _index: lookup(), range(32)))

    assert results == [None] * 32
    assert calls
    assert len(calls) <= 32
    assert "THREAD.NS" in market_data._NEGATIVE_METADATA_CACHE
    assert len(market_data._NEGATIVE_METADATA_CACHE) == 1


def test_negative_metadata_cache_refreshes_lru_recency(monkeypatch) -> None:
    market_data.clear_market_metadata_cache()
    limit = market_data._NEGATIVE_METADATA_CACHE_MAX_ENTRIES
    calls: list[str] = []

    class FakeTicker:
        def __init__(self, ticker: str, **_kwargs) -> None:
            self.ticker = ticker

        @property
        def fast_info(self) -> dict[str, None]:
            calls.append(self.ticker)
            return {"market_cap": None}

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)
    for index in range(limit):
        assert market_data.get_market_cap(f"S{index}.NS", negative_cache_ttl_seconds=60) is None

    # Touch the oldest key so it becomes most recently used.
    assert market_data.get_market_cap("S0.NS", negative_cache_ttl_seconds=60) is None
    assert calls.count("S0.NS") == 1

    assert market_data.get_market_cap(f"S{limit}.NS", negative_cache_ttl_seconds=60) is None
    assert len(market_data._NEGATIVE_METADATA_CACHE) == limit
    assert "S0.NS" in market_data._NEGATIVE_METADATA_CACHE
    assert "S1.NS" not in market_data._NEGATIVE_METADATA_CACHE
