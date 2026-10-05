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
