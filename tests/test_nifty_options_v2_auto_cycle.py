from datetime import date

from engine.nifty_options_v2_auto import NiftyOptionsV2AutoPaper, PaperAction
from engine.nifty_options_v2_live import LivePaperObservation
from engine.nifty_options_v2_market_data import NiftyV2MarketObservation
from strategy.nifty_options_v2 import NiftyCallContract


def test_auto_paper_handles_no_active_trade() -> None:
    observation = NiftyV2MarketObservation(
        contract=NiftyCallContract(expiry=date(2026, 10, 29), strike=24000),
        observation=LivePaperObservation(
            observed_date=date(2026, 10, 20),
            spot=25000,
            ltp=1000,
        ),
    )

    decision = NiftyOptionsV2AutoPaper().process(
        observation=observation,
        current_series_expiry=date(2026, 10, 29),
    )

    assert decision.action is PaperAction.HOLD


from engine.nifty_options_v2_auto_cycle import NiftyOptionsV2AutoCycle


EXPIRIES = ("2026-10-29", "2026-11-26")


def _observation(
    *,
    observed_date: date,
    expiry: date,
) -> NiftyV2MarketObservation:
    return NiftyV2MarketObservation(
        contract=NiftyCallContract(expiry=expiry, strike=24000),
        observation=LivePaperObservation(
            observed_date=observed_date,
            spot=25000,
            ltp=1000,
        ),
    )


def test_coordinator_returns_hold_before_expiry() -> None:
    result = NiftyOptionsV2AutoCycle().process(
        expiries=EXPIRIES,
        observed_date=date(2026, 10, 20),
        observation=_observation(
            observed_date=date(2026, 10, 20),
            expiry=date(2026, 11, 26),
        ),
    )

    assert result is not None
    assert result.action is PaperAction.HOLD
    assert result.current_expiry == date(2026, 10, 29)
    assert result.next_expiry == date(2026, 11, 26)


def test_coordinator_enters_next_series_on_expiry() -> None:
    result = NiftyOptionsV2AutoCycle().process(
        expiries=EXPIRIES,
        observed_date=date(2026, 10, 29),
        observation=_observation(
            observed_date=date(2026, 10, 29),
            expiry=date(2026, 11, 26),
        ),
    )

    assert result is not None
    assert result.action is PaperAction.ENTER_NEXT_SERIES


def test_coordinator_returns_none_without_two_expiries() -> None:
    result = NiftyOptionsV2AutoCycle().process(
        expiries=("2026-10-29",),
        observed_date=date(2026, 10, 20),
        observation=_observation(
            observed_date=date(2026, 10, 20),
            expiry=date(2026, 11, 26),
        ),
    )

    assert result is None
