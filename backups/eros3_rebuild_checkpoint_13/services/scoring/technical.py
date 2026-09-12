from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.market_data.models import PriceRecord


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    return max(minimum, min(maximum, float(value)))


def _sma(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    if len(values) < period:
        return sum(values) / len(values)
    return sum(values[-period:]) / period


def _ema(
    values: list[float],
    period: int,
) -> float:
    if not values:
        return 0.0
    if len(values) < period:
        return sum(values) / len(values)
    multiplier = 2.0 / (period + 1.0)
    ema_value = sum(values[:period]) / period
    for value in values[period:]:
        ema_value = (value - ema_value) * multiplier + ema_value
    return ema_value


def _calculate_rsi(
    closes: list[float],
    period: int = 14,
) -> float:
    if len(closes) <= period:
        return 50.0
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))
    recent_gains = gains[-period:]
    recent_losses = losses[-period:]
    avg_gain = sum(recent_gains) / period
    avg_loss = sum(recent_losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _calculate_macd(
    closes: list[float],
) -> tuple[float, float, float]:
    if not closes:
        return 0.0, 0.0, 0.0
    macd = _ema(closes, 12) - _ema(closes, 26)
    signal_window = min(9, max(1, len(closes)))
    macd_series: list[float] = []
    for i in range(1, len(closes) + 1):
        subset = closes[:i]
        value = _ema(subset, 12) - _ema(subset, 26)
        macd_series.append(value)
    signal = _ema(
        macd_series,
        signal_window,
    )
    histogram = macd - signal
    return macd, signal, histogram


@dataclass(frozen=True, slots=True)
class TechnicalIndicatorResult:
    sma_20: float
    sma_50: float
    sma_200: float
    rsi_14: float
    macd: float
    macd_signal: float
    macd_histogram: float
    trend_score: float
    relative_strength_score: float
    breakout_score: float
    momentum_score: float


@dataclass(frozen=True, slots=True)
class MomentumScoreResult:
    symbol: str
    momentum_score: float
    trend_score: float
    rsi_score: float
    macd_score: float
    moving_average_score: float
    relative_strength_score: float
    breakout_score: float
    details: dict[str, Any]


class TechnicalIndicatorEngine:
    """
    EROS 3.0 technical indicator engine.
    Calculates deterministic indicators from OHLCV PriceRecord data.
    """

    def calculate(
        self,
        records: list[PriceRecord],
    ) -> TechnicalIndicatorResult:
        closes = [float(record.close) for record in records]
        if not closes:
            return TechnicalIndicatorResult(
                sma_20=0.0,
                sma_50=0.0,
                sma_200=0.0,
                rsi_14=50.0,
                macd=0.0,
                macd_signal=0.0,
                macd_histogram=0.0,
                trend_score=50.0,
                relative_strength_score=50.0,
                breakout_score=50.0,
                momentum_score=50.0,
            )
        sma_20 = _sma(closes, 20)
        sma_50 = _sma(closes, 50)
        sma_200 = _sma(closes, 200)
        rsi_14 = _calculate_rsi(
            closes,
            14,
        )
        macd, macd_signal, macd_histogram = _calculate_macd(closes)
        current_price = closes[-1]

        # Trend
        trend_score = 50.0
        if current_price > sma_20:
            trend_score += 15.0
        if current_price > sma_50:
            trend_score += 15.0
        if current_price > sma_200:
            trend_score += 20.0
        trend_score = _clamp(trend_score)

        # Relative Strength
        if len(closes) >= 20:
            old_price = closes[-20]
        else:
            old_price = closes[0]
        if old_price > 0:
            return_20 = (current_price / old_price) - 1.0
        else:
            return_20 = 0.0
        relative_strength_score = _clamp(50.0 + return_20 * 200.0)

        # Breakout
        if len(closes) >= 20:
            prior_window = closes[-20:-1]
        else:
            prior_window = closes[:-1]
        if prior_window:
            previous_high = max(prior_window)
            if current_price > previous_high:
                breakout_score = 100.0
            elif previous_high > 0:
                distance = current_price / previous_high
                breakout_score = _clamp(50.0 + (distance - 0.95) * 1000.0)
            else:
                breakout_score = 50.0
        else:
            breakout_score = 50.0

        # Momentum
        rsi_score = _clamp(50.0 + (rsi_14 - 50.0) * 1.2)
        if macd_histogram > 0:
            macd_score = 75.0
        elif macd_histogram < 0:
            macd_score = 25.0
        else:
            macd_score = 50.0
        moving_average_score = _clamp(
            (trend_score + (50.0 if current_price >= sma_20 else 25.0)) / 2.0
        )
        momentum_score = round(
            trend_score * 0.25
            + rsi_score * 0.20
            + macd_score * 0.20
            + moving_average_score * 0.15
            + relative_strength_score * 0.10
            + breakout_score * 0.10,
            2,
        )
        return TechnicalIndicatorResult(
            sma_20=round(sma_20, 4),
            sma_50=round(sma_50, 4),
            sma_200=round(sma_200, 4),
            rsi_14=round(rsi_14, 4),
            macd=round(macd, 4),
            macd_signal=round(macd_signal, 4),
            macd_histogram=round(
                macd_histogram,
                4,
            ),
            trend_score=round(
                trend_score,
                2,
            ),
            relative_strength_score=round(
                relative_strength_score,
                2,
            ),
            breakout_score=round(
                breakout_score,
                2,
            ),
            momentum_score=momentum_score,
        )


class MomentumScoringEngine:
    """
    Converts technical indicators into the EROS
    institutional momentum scoring contract.
    """

    def evaluate(
        self,
        symbol: str,
        records: list[PriceRecord],
    ) -> MomentumScoreResult:
        technical = TechnicalIndicatorEngine().calculate(records)
        rsi_score = _clamp(50.0 + (technical.rsi_14 - 50.0) * 1.2)
        if technical.macd_histogram > 0:
            macd_score = 75.0
        elif technical.macd_histogram < 0:
            macd_score = 25.0
        else:
            macd_score = 50.0
        moving_average_score = technical.trend_score
        momentum_score = round(
            technical.trend_score * 0.25
            + rsi_score * 0.20
            + macd_score * 0.20
            + moving_average_score * 0.15
            + technical.relative_strength_score * 0.10
            + technical.breakout_score * 0.10,
            2,
        )
        details = {
            "engine_version": "EROS-3.0-BLOCK-14",
            "records_analyzed": len(records),
            "indicators": {
                "sma_20": technical.sma_20,
                "sma_50": technical.sma_50,
                "sma_200": technical.sma_200,
                "rsi_14": technical.rsi_14,
                "macd": technical.macd,
                "macd_signal": technical.macd_signal,
                "macd_histogram": technical.macd_histogram,
            },
        }
        return MomentumScoreResult(
            symbol=symbol,
            momentum_score=momentum_score,
            trend_score=technical.trend_score,
            rsi_score=round(rsi_score, 2),
            macd_score=round(macd_score, 2),
            moving_average_score=round(
                moving_average_score,
                2,
            ),
            relative_strength_score=(technical.relative_strength_score),
            breakout_score=technical.breakout_score,
            details=details,
        )
