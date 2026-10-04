from datetime import date

from engine.nifty_options_v2_backtest import NiftyOptionsV2Backtest
from engine.nifty_options_v2_pipeline import NiftyOptionsV2Pipeline, V2SeriesInput
from strategy.nifty_options_v2 import NiftyCallContract, NiftyCallObservation


class FakeData:
    rows = {
        date(2021, 5, 27): NiftyCallObservation(
            NiftyCallContract(date(2021, 6, 24), 15000), date(2021, 5, 27), 15300, 420
        ),
        date(2021, 6, 24): NiftyCallObservation(
            NiftyCallContract(date(2021, 6, 24), 15000), date(2021, 6, 24), 15700, 760
        ),
    }

    def get_observation(self, *, expiry, strike, observed_date):
        return self.rows[observed_date]


def test_pipeline_selects_strike_runs_trade_and_reports() -> None:
    trades, report = NiftyOptionsV2Pipeline(NiftyOptionsV2Backtest(FakeData())).run(
        [
            V2SeriesInput(
                series="2021-06",
                expiry=date(2021, 6, 24),
                entry_date=date(2021, 5, 27),
                exit_date=date(2021, 6, 24),
                spot_entry=15300,
                available_strikes=[14500, 15000, 15500],
            )
        ]
    )
    assert len(trades) == 1
    assert trades[0].trade.entry.contract.strike == 14500
    assert report.total_points == 340
    assert report.winning_months == 1


def test_pipeline_rejects_when_no_itm_strike_exists() -> None:
    pipeline = NiftyOptionsV2Pipeline(NiftyOptionsV2Backtest(FakeData()))
    try:
        pipeline.run(
            [
                V2SeriesInput(
                    "2021-06", date(2021, 6, 24), date(2021, 5, 27), date(2021, 6, 24),
                    15300, [15300, 15500],
                )
            ]
        )
    except ValueError as exc:
        assert "no ITM" in str(exc)
    else:
        raise AssertionError("expected no-ITM validation failure")
