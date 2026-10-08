"""Configurable India-equity transaction cost estimates for research backtests.

Rates are user-configurable basis points of traded notional. They are not a
live statutory rate feed; update them for the broker, exchange, product and
date being tested.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class IndiaEquityCostModel:
    """Estimate per-side equity trading costs as fractions of portfolio value."""

    brokerage_bps: float = 0.0
    exchange_transaction_bps: float = 0.0
    regulatory_bps: float = 0.0
    stt_buy_bps: float = 0.0
    stt_sell_bps: float = 0.0
    stamp_duty_buy_bps: float = 0.0
    slippage_bps: float = 0.0
    gst_rate: float = 0.18

    def __post_init__(self) -> None:
        rates = (
            self.brokerage_bps,
            self.exchange_transaction_bps,
            self.regulatory_bps,
            self.stt_buy_bps,
            self.stt_sell_bps,
            self.stamp_duty_buy_bps,
            self.slippage_bps,
        )
        if any(rate < 0 for rate in rates):
            raise ValueError("cost rates must be non-negative")
        if not 0 <= self.gst_rate <= 1:
            raise ValueError("gst_rate must be between zero and one")

    def cost_fraction(
        self,
        buy_turnover: pd.Series,
        sell_turnover: pd.Series,
    ) -> pd.Series:
        """Return per-bar cost fractions for buy and sell traded notional."""
        brokerage = self.brokerage_bps / 10_000.0
        exchange = self.exchange_transaction_bps / 10_000.0
        regulatory = self.regulatory_bps / 10_000.0
        slippage = self.slippage_bps / 10_000.0
        gst = self.gst_rate * (brokerage + exchange + regulatory)
        buy_rate = (
            brokerage
            + exchange
            + regulatory
            + gst
            + self.stt_buy_bps / 10_000.0
            + self.stamp_duty_buy_bps / 10_000.0
            + slippage
        )
        sell_rate = (
            brokerage
            + exchange
            + regulatory
            + gst
            + self.stt_sell_bps / 10_000.0
            + slippage
        )
        return buy_turnover * buy_rate + sell_turnover * sell_rate
